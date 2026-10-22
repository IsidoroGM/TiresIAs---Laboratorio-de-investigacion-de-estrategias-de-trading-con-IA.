"""La consulta conserva los resultados guardados y no puede iniciar trabajo nuevo."""

from copy import deepcopy
from hashlib import sha256
import http.client
import json
from pathlib import Path
import socket
import threading

import pytest

from trading_ai.lab import create_server
from trading_ai.lab_catalog import Catalog
from trading_ai.lab_query import LabQuery, usage_totals


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


@pytest.fixture
def lab(tmp_path):
    run = tmp_path / ".local/research/sample"
    policy = {"pair": "EUR/USD", "baseline_strategy": "sma", "fast_window": 2, "slow_window": 3,
              "initial_capital": "1000", "cost_rate": "0.001", "allocation_fraction": "0.1"}
    data = {"sha256": "1" * 64, "first_date": "2020-01-02", "last_date": "2020-01-03", "observations": 2}
    summary = {"strategy": "SMA2/SMA3", "quote_currency": "USD", "final_equity": "990",
               "return_percent": "-1", "max_drawdown_percent": "1", "closed_trades": 0,
               "has_open_position": True, "total_costs": "0.1", "rejected_entries": 0}
    points = [{"date": day, "cash": "900", "position_value": value, "equity": equity,
               "drawdown": dd, "drawdown_percent": pct}
              for day, value, equity, dd, pct in (("2020-01-02", "100", "1000", "0", "0"),
                                                 ("2020-01-03", "90", "990", "10", "1"))]
    bt = {"pair": "EUR/USD", "quote_currency": "USD", "initial_capital": "1000",
          "cost_rate": "0.001", "allocation_fraction": "0.1", "closed_trades": [],
          "open_position": {"entry_date": "2020-01-02", "quantity": "10"}, "equity_curve": points}
    for role in ("baseline", "candidate"):
        save(run / (role + ".json"), {"summary": summary, "backtest": bt})
    value = {"source": data, "policy": policy,
             "proposal": {"hypothesis": "<script>window.executed=true</script>", "criterion": "higher_return_without_more_drawdown",
                          "arguments": {"strategy": "ema", "fast_window": 2, "slow_window": 3}},
             "baseline": summary, "candidate": summary,
             "artifacts_sha256": {role + ".json": sha256((run / (role + ".json")).read_bytes()).hexdigest()
                                  for role in ("baseline", "candidate")}}
    save(run / "results.json", value)
    events = [{"at": "2026-10-20T10:00:00+00:00", "event": "run_started", "data": {"policy": policy}},
              {"at": "2026-10-20T10:01:00+00:00", "event": "model_response", "data": {"content": "<img src=x onerror=alert(1)>",
                       "usage": {"input_tokens": 14, "output_tokens": 3, "api_cost_usd": "0"}}},
              {"at": "2026-10-20T10:02:00+00:00", "event": "run_completed", "data": {"model_requests": 1, "api_cost_usd": "0"}}]
    (run / "events.jsonl").write_text("\n".join(json.dumps(event) for event in events), encoding="utf-8")
    archive = tmp_path / "reports/phase-test"
    files = {}
    for path in run.iterdir():
        raw = path.read_bytes()
        target = archive / "run" / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        files["run/" + path.name] = {"source": str(path), "sha256": sha256(raw).hexdigest()}
    save(archive / "snapshot.json", {"schema_version": 1, "files": files})
    (tmp_path / "reports/phase-test.md").write_text("# Informe histórico\n", encoding="utf-8")
    return tmp_path, run, archive


def local(query):
    return next(item for item in query.experiments()["items"] if item["origin"] == "local")


def fingerprint(root):
    return {str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest() for path in root.rglob("*") if path.is_file()}


def test_catalog_filters_and_independent_provenance(lab):
    root, _, _ = lab
    q = LabQuery(root)
    rows = q.experiments()["items"]
    assert {item["origin"] for item in rows} == {"local", "archive"}
    assert len(q.experiments({"pair": "EUR/USD", "strategy": "EMA", "date": "2026-10-20", "origin": "local", "state": "run_completed"})["items"]) == 1
    assert not q.experiments({"pair": "USD/JPY"})["items"]
    assert len(q.home()["reports"]) == 1


def test_saved_results_and_original_model_text_are_preserved(lab):
    root, _, _ = lab
    q = LabQuery(root)
    d = q.detail(local(q)["id"])
    assert d["hypothesis"] == "<script>window.executed=true</script>"
    assert d["model"][0]["content"] == "<img src=x onerror=alert(1)>"
    assert d["python"] == []
    assert d["results_certified"] is False
    a = q.account(d["id"], d["accounts"][0]["id"])
    assert a["backtest"]["equity_curve"][-1]["equity"] == "990"
    assert a["summary"]["return_percent"] == "-1"
    assert a["independent_account"] is True
    assert d["usage"]["new"] == {"model_requests": 1, "input_tokens": 14, "output_tokens": 3, "api_cost_usd": "0"}


def test_archive_survives_missing_originals(lab):
    root, run, _ = lab
    for path in run.iterdir(): path.unlink()
    q = LabQuery(root)
    row = next(item for item in q.experiments()["items"] if item["origin"] == "archive")
    d = q.detail(row["id"])
    assert d["integrity"]["state"] == "copies_verified"
    assert d["origin"] == "archive"
    assert d["manifest"]
    assert q.account(d["id"], d["accounts"][0]["id"])["backtest"]


@pytest.mark.parametrize("mode", ["changed_copy", "missing_copy", "changed_original"])
def test_alterations_are_visible_and_do_not_substitute_files(lab, mode):
    root, run, archive = lab
    target = (run if mode == "changed_original" else archive / "run") / "results.json"
    if mode == "missing_copy": target.unlink()
    else:
        value = json.loads(target.read_text(encoding="utf-8"))
        value["proposal"]["hypothesis"] = "Alterado"
        save(target, value)
    q = LabQuery(root)
    row = next(item for item in q.experiments()["items"] if item["origin"] == ("local" if mode == "changed_original" else "archive"))
    d = q.detail(row["id"])
    assert d["integrity"]["state"] in ("changed", "unverifiable")
    assert d["results_certified"] is False
    if mode != "missing_copy": assert d["hypothesis"] == "Alterado"


def test_altered_account_not_hidden_by_unchanged_summary(lab):
    root, run, _ = lab
    value = json.loads((run / "baseline.json").read_text(encoding="utf-8"))
    value["backtest"]["equity_curve"][-1]["equity"] = "99999"
    save(run / "baseline.json", value)
    q = LabQuery(root)
    d = q.detail(local(q)["id"])
    a = q.account(d["id"], d["accounts"][0]["id"])
    assert a["backtest"] is None
    assert a["integrity"]["state"] == "unverifiable"


def test_summary_only_does_not_recalculate_details(lab):
    root, run, _ = lab
    (run / "baseline.json").unlink()
    q = LabQuery(root)
    d = q.detail(local(q)["id"])
    a = q.account(d["id"], d["accounts"][0]["id"])
    assert a["backtest"] is None
    assert a["summary"]["final_equity"] == "990"


@pytest.mark.parametrize("area,field,value", [("policy", "pair", "USD/JPY"), ("policy", "initial_capital", "2000"),
                                               ("policy", "cost_rate", "0.1"), ("policy", "allocation_fraction", None),
                                               ("source", "sha256", "2" * 64), ("source", "first_date", "2019-01-01")])
def test_comparison_rejects_different_sources_or_controls(lab, area, field, value):
    root, run, _ = lab
    value2 = json.loads((run / "results.json").read_text(encoding="utf-8"))
    value2[area][field] = value
    second = run.parent / "second"
    save(second / "results.json", value2)
    (second / "events.jsonl").write_bytes((run / "events.jsonl").read_bytes())
    q = LabQuery(root)
    rows = [x for x in q.experiments()["items"] if x["origin"] == "local"]
    left, right = (q.detail(row["id"]) for row in rows)
    compared = q.compare(left["id"], left["accounts"][0]["id"], right["id"], right["accounts"][0]["id"])
    assert compared["compatible"] is False


def test_comparison_accepts_same_controls_but_keeps_accounts_separate(lab):
    root, _, _ = lab
    q = LabQuery(root)
    d = q.detail(local(q)["id"])
    result = q.compare(d["id"], d["accounts"][0]["id"], d["id"], d["accounts"][1]["id"])
    assert result["compatible"] is True
    assert len(result["accounts"]) == 2
    assert result["strategy_differences"]["left"] != result["strategy_differences"]["right"]
    assert "total_equity" not in result


@pytest.mark.parametrize("raw", [b'{"source":', b'{"policy":{},"policy":{}}', b'{"baseline":NaN}', b'[]'])
def test_invalid_json_remains_visible(lab, raw):
    root, run, _ = lab
    (run / "results.json").write_bytes(raw)
    q = LabQuery(root)
    row = local(q)
    assert row["state"] == "unreadable"
    assert q.detail(row["id"])["warnings"]


def test_event_only_attempt_is_incomplete_without_invented_progress(lab):
    root, _, _ = lab
    path = root / ".local/campaign-cycles/interrupted/events.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"event": "cycle_started", "at": "2026-10-20T10:00:00+00:00", "data": {}}), encoding="utf-8")
    q = LabQuery(root)
    row = next(item for item in q.experiments()["items"] if item["kind"] == "campaign-cycles")
    d = q.detail(row["id"])
    assert d["state"] == "incomplete"
    assert d["integrity"]["state"] == "incomplete"
    assert not d["accounts"]
    assert d["usage"]["new"]["input_tokens"] is None
    assert "progress" not in d


def test_consumption_deduplicates_copies_and_separates_inherited(lab):
    root, run, _ = lab
    value = json.loads((run / "results.json").read_text(encoding="utf-8"))
    value["usage"] = {"usage": {"model_requests": 1, "input_tokens": None, "output_tokens": 180, "api_cost_usd": "0"},
                      "inherited_usage": [{"input_tokens": 2262, "output_tokens": 176}], "known_subtotals": {"input_tokens": 2898}}
    save(run / "results.json", value)
    result = LabQuery(root).consumption()
    assert len(result["items"]) == 1
    row = result["items"][0]
    assert row["new"]["input_tokens"] is None
    assert row["inherited"][0]["input_tokens"] == 2262
    assert row["known_subtotals"]["input_tokens"] == 2898
    assert usage_totals([])["input_tokens"] is None
    assert usage_totals([{"input_tokens": 0}])["input_tokens"] == 0


def test_arbitrary_references_and_private_folders_are_never_read(lab, monkeypatch):
    root, run, archive = lab
    private = root / ".local/models/secret.json"
    save(private, {"private": True})
    value = json.loads((run / "results.json").read_text(encoding="utf-8"))
    value.update(protocol="known_walk_forward_result_v1", plan={"directory": str(private.parent)}, folds=[])
    save(run / "results.json", value)
    original = Path.open
    def guarded(path, *args, **kwargs):
        assert path != private
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    q = LabQuery(root)
    q.detail(local(q)["id"])
    with pytest.raises(ValueError): q.catalog.read(private)
    with pytest.raises(ValueError): q.catalog.read(root / "README.md")
    with pytest.raises(ValueError): q.catalog.read(root / "reports/../../secret")


@pytest.mark.parametrize("name", ["../outside.json", "C:\\outside.json", "run/../../outside.json"])
def test_manifest_cannot_escape_its_directory(lab, name):
    root, _, archive = lab
    save(archive / "snapshot.json", {"schema_version": 1, "files": {name: {"source": ".local/research/a/results.json", "sha256": "1" * 64}}})
    q = LabQuery(root)
    assert q.catalog.warnings
    assert not any(item["origin"] == "archive" for item in q.experiments()["items"])


def test_symlink_source_is_rejected(lab, monkeypatch):
    root, run, _ = lab
    source = run / "extra.json"
    # Windows puede exigir privilegios para crear enlaces. Se ejercita la guarda
    # de resolución sin depender de esos privilegios ni cambiar permisos del equipo.
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == source or original(path))
    with pytest.raises(ValueError): Catalog(root).read(source)


def test_legacy_archive_is_checked_without_rewriting_it(lab):
    root, _, archive = lab
    value = json.loads((archive / "snapshot.json").read_text(encoding="utf-8"))
    save(archive / "snapshot.json", {"date": "2026-10-19", "files": [{"snapshot": name, **item} for name, item in value["files"].items()]})
    before = fingerprint(root)
    q = LabQuery(root)
    row = next(item for item in q.experiments()["items"] if item["origin"] == "archive")
    assert q.detail(row["id"])["integrity"]["scope"] == "legacy_file_integrity_only"
    assert before == fingerprint(root)


def test_queries_never_infer_reserve_or_backtest(lab, monkeypatch):
    from trading_ai import ai, backtesting, campaign_cycle, campaign_ledger, rule_execution
    def denied(*args, **kwargs): raise AssertionError("La consulta intentó iniciar trabajo nuevo")
    monkeypatch.setattr(ai.OllamaProvider, "complete", denied)
    monkeypatch.setattr(ai, "create_provider", denied)
    monkeypatch.setattr(backtesting, "run_backtest", denied)
    monkeypatch.setattr(rule_execution, "_calculate", denied)
    monkeypatch.setattr(campaign_cycle, "run_cycle", denied)
    monkeypatch.setattr(campaign_ledger, "reserve_proposal", denied)
    monkeypatch.setattr(campaign_ledger, "reserve_comparison", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    root, _, _ = lab
    before = fingerprint(root)
    q = LabQuery(root)
    q.home(); q.experiments(); q.consumption()
    for row in q.experiments()["items"]:
        d = q.detail(row["id"])
        for account in d["accounts"]: q.account(d["id"], account["id"])
    assert before == fingerprint(root)


@pytest.fixture
def server(lab):
    root, _, _ = lab
    server = create_server(root=root, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try: yield server
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=3)


def request(server, path, method="GET", headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
    try:
        connection.request(method, path, headers=headers or {})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally: connection.close()


def test_http_navigation_sources_and_security_headers(server):
    assert server.server_address[0] == "127.0.0.1"
    for path in ("/", "/app.js", "/style.css", "/api/home", "/api/experiments", "/api/consumption"):
        status, headers, raw = request(server, path)
        assert status == 200
        assert raw
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert "script-src 'self'" in headers["Content-Security-Policy"]
    rows = json.loads(request(server, "/api/experiments")[2])["items"]
    detail = json.loads(request(server, "/api/experiments/" + rows[0]["id"])[2])
    source = detail["files"][0]
    status, headers, _ = request(server, "/sources/" + source["id"])
    assert status == 200
    assert headers["Content-Type"] == "text/plain; charset=utf-8"
    assert request(server, "/api/experiments", "HEAD")[2] == b""


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
def test_http_has_no_execution_or_mutation_endpoints(server, method):
    assert request(server, "/api/run", method)[0] == 405


@pytest.mark.parametrize("headers", [{"Host": "attacker.example"}, {"Origin": "https://attacker.example"}, {"Origin": "null"}])
def test_http_rejects_remote_hosts_and_origins(server, headers):
    assert request(server, "/api/home", headers=headers)[0] == 403


@pytest.mark.parametrize("path", ["/sources/../../README.md", "/sources/not-an-id", "/api/run", "/api/experiments/not-an-id", "/.env"])
def test_http_only_serves_catalogued_files(server, path):
    assert request(server, path)[0] == 404


def test_empty_project_is_a_valid_empty_view(tmp_path):
    q = LabQuery(tmp_path)
    assert q.home()["counts"]["experiments"] == 0
    assert q.consumption()["items"] == []


def test_walk_forward_keeps_windows_separate_and_does_not_force_a_winner(lab):
    root, run, _ = lab
    saved = json.loads((run / "results.json").read_text(encoding="utf-8"))
    plan_dir = root / ".local/walk-forward-plans/plan"
    plan = {"policy": saved["policy"], "criterion": saved["proposal"]["criterion"],
            "candidates": [{"id": "candidate", "strategy": "ema", "fast_window": 2, "slow_window": 3}],
            "folds": [{"index": 1, "train": saved["source"], "check": {**saved["source"], "sha256": "2" * 64}}]}
    save(plan_dir / "plan.json", plan)
    directory = root / ".local/walk-forward-runs/run"
    save(directory / "results.json", {"protocol": "known_walk_forward_result_v1", "plan": {"directory": str(plan_dir)},
                                       "folds": [{"index": 1, "selected_id": None, "train_baseline": saved["baseline"],
                                                  "train_candidates": {"candidate": saved["candidate"]}, "check": None}]})
    (directory / "events.jsonl").write_bytes((run / "events.jsonl").read_bytes())
    q = LabQuery(root)
    row = next(item for item in q.experiments({"pair": "EUR/USD"})["items"] if item["kind"] == "walk-forward-runs")
    detail = q.detail(row["id"])
    assert len(detail["accounts"]) == 2
    assert all("entrenamiento" in account["label"] for account in detail["accounts"])
    assert all(account["independent_account"] for account in detail["accounts"])


def test_evaluation_uses_saved_block_sources(lab):
    root, run, _ = lab
    saved = json.loads((run / "results.json").read_text(encoding="utf-8"))
    value = {"policy": saved["policy"], "proposal": saved["proposal"],
             "blocks": {"development": {"results": saved}, "evaluation": {"results": {**saved, "source": {**saved["source"], "sha256": "3" * 64}}}}}
    save(run / "results.json", value)
    q = LabQuery(root)
    detail = q.detail(local(q)["id"])
    assert len(detail["accounts"]) == 4
    result = q.compare(detail["id"], detail["accounts"][0]["id"], detail["id"], detail["accounts"][2]["id"])
    assert not result["compatible"]
    assert "data.sha256" in result["differences"]


def test_sensitivity_preserves_each_scenarios_costs(lab):
    root, run, _ = lab
    saved = json.loads((run / "results.json").read_text(encoding="utf-8"))
    row = {"scenario": {"id": "cost-variant"}, "result": {**saved, "policy": {**saved["policy"], "cost_rate": "0.002"}}}
    save(run / "results.json", {"plan": {"reference_policy": saved["policy"]}, "rows": {"check": [row]}})
    q = LabQuery(root)
    detail = q.detail(local(q)["id"])
    assert len(detail["accounts"]) == 2
    assert all(account["policy"]["cost_rate"] == "0.002" for account in detail["accounts"])


def test_capture_usage_and_content_are_read_from_the_recorded_observation(lab):
    root, _, _ = lab
    directory = root / ".local/campaign-attempts/capture"
    save(directory / "completion.json", {"status": "observation_recorded", "analysis": {
        "usage": {"model_requests": 1, "input_tokens": 2898, "output_tokens": 180, "api_cost_usd": "0"}}})
    (directory / "observation.raw").write_text(json.dumps({"content": "<script>throw Error()</script>"}), encoding="utf-8")
    q = LabQuery(root)
    row = next(item for item in q.experiments()["items"] if item["kind"] == "campaign-attempts")
    detail = q.detail(row["id"])
    assert detail["model"][0]["content"] == "<script>throw Error()</script>"
    assert detail["usage"]["new"]["input_tokens"] == 2898


def test_evidence_links_reach_the_inventory_and_original_report(lab):
    root, _, _ = lab
    q = LabQuery(root)
    detail = q.detail(local(q)["id"])
    assert {file["path"] for file in detail["evidence"]} == {"reports/phase-test/snapshot.json", "reports/phase-test.md"}


@pytest.mark.parametrize("field,value", [("initial_capital", "NaN"), ("cost_rate", "-0.1"), ("allocation_fraction", "2")])
def test_identical_invalid_controls_do_not_make_results_comparable(lab, field, value):
    root, run, _ = lab
    saved = json.loads((run / "results.json").read_text(encoding="utf-8"))
    saved["policy"][field] = value
    save(run / "results.json", saved)
    q = LabQuery(root)
    detail = q.detail(local(q)["id"])
    result = q.compare(detail["id"], detail["accounts"][0]["id"], detail["id"], detail["accounts"][1]["id"])
    assert not result["compatible"]
    assert "invalid_policy" in result["differences"]
