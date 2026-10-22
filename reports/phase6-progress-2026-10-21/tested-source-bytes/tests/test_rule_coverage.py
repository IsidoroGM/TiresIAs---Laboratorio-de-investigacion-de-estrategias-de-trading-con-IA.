"""Cobertura estática: variar números no prueba novedad y compartir plantilla no prueba equivalencia."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from test_compact_candidate import isolated_history, prepared_request, transport
from test_compact_review import isolated_reviews, candidate
from test_discovery import registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from test_structured_session import session
from test_structured_draft_request import memory
from trading_ai.compact_history import capture_compact_history
from trading_ai.rule_coverage import capture_rule_coverage, profile_rule, verify_rule_coverage, main
from trading_ai.structured_ideas import compile_proposal
from trading_ai import rule_coverage as coverage


def test_profile_is_pure_and_technical_name_does_not_define_new_rule(proposal, monkeypatch):
    spec = compile_proposal(proposal).to_spec()
    before = deepcopy(spec)
    def forbidden(*args): pytest.fail("Perfilar no debe calcular señales")
    monkeypatch.setattr("trading_ai.rules.RuleStrategy.generate_signals", forbidden)
    first = profile_rule(spec)
    assert spec == before
    spec["name"] = "another_name"
    assert profile_rule(spec) == first
    assert first["semantic_equivalence_proven"] is first["performance_or_novelty_proven"] is False


@pytest.mark.parametrize("change", ["value", "lag", "window"])
def test_numeric_changes_preserve_template_but_not_rule_identity_or_parameters(proposal, change):
    if change == "window": proposal["entry"]["right"] = {"kind": "ema", "window": 20, "lag": 0}
    first = compile_proposal(proposal).to_spec()
    second = deepcopy(first)
    condition = second["entry"]["conditions"][0]
    if change == "value": condition["right"]["value"] = "2"
    elif change == "lag": condition["left"]["lag"] = 1
    else: condition["right"]["window"] = 21
    a, b = profile_rule(first), profile_rule(second)
    assert a["rule_identity_without_name"] != b["rule_identity_without_name"]
    assert a["template_identity_without_numeric_parameters"] == b["template_identity_without_numeric_parameters"]
    assert a["parameters"] != b["parameters"]


@pytest.mark.parametrize("change", ["operator", "sides", "kind", "group"])
def test_roles_operators_kinds_and_groups_remain_in_template(proposal, change):
    first = compile_proposal(proposal).to_spec()
    second = deepcopy(first)
    condition = second["entry"]["conditions"][0]
    if change == "operator": condition["operator"] = "gte"
    elif change == "sides": condition["left"], condition["right"] = condition["right"], condition["left"]
    elif change == "kind": condition["left"] = {"kind": "sma", "window": 20, "lag": 0}
    else: second["entry"]["match"] = "any"
    assert profile_rule(first)["template_identity_without_numeric_parameters"] != profile_rule(second)["template_identity_without_numeric_parameters"]


def test_invalid_specs_are_validated_before_profile_generation(proposal):
    spec = compile_proposal(proposal).to_spec()
    spec["entry"]["conditions"][0]["left"]["lag"] = -1
    with pytest.raises(ValueError): profile_rule(spec)


@pytest.fixture
def sources(candidate, prepared_request, memory, tmp_path):
    context = Path(json.loads((memory / "reviews.json").read_bytes())["context"]["directory"])
    history = capture_compact_history(prepared_request, output_dir=tmp_path / "compact-memory")
    return context, history


def test_capture_groups_variants_without_selection_or_performance_claims(sources, tmp_path, monkeypatch):
    context, history = sources
    def forbidden(*args, **kwargs): pytest.fail("La cobertura no debe consultar, simular o aprobar")
    for name in ("trading_ai.rules.RuleStrategy.generate_signals", "trading_ai.rule_execution._calculate",
                 "trading_ai.compact_ollama.CompactOllamaProvider.complete", "socket.socket.connect"):
        monkeypatch.setattr(name, forbidden)
    run = capture_rule_coverage(context, history_dir=history, output_dir=tmp_path / "coverage")
    record = verify_rule_coverage(run)
    assert record["counts"] == {"record_occurrences": 2, "distinct_rule_identities_without_name": 2,
                                "distinct_templates_without_numeric_parameters": 1, "repeated_rule_occurrences": 0}
    assert record["free_text_ideas_analyzed"] is record["global_history_complete"] is False
    assert record["observed_direct_operand_kinds"] == ["constant", "reference"]
    assert "rolling_min" in record["direct_operand_kinds_not_observed"]
    assert record["semantic_equivalence_proven"] is record["strategy_novelty_proven"] is record["strategy_selected"] is False
    assert record["eligible_for_plan"] is record["executable"] is False and record["calculated_results"] is None
    assert record["new_usage"]["model_requests"] == record["new_usage"]["backtests"] == 0


def test_context_only_capture_is_scoped_to_typed_rules(sources, tmp_path):
    run = capture_rule_coverage(sources[0], output_dir=tmp_path / "coverage")
    record = verify_rule_coverage(run)
    assert record["source_history"] is None and record["counts"]["record_occurrences"] == 1


@pytest.mark.parametrize("filename", ["coverage.json", "coverage.json.sha256", "report.md", "events.jsonl"])
def test_changed_diagnostic_is_rejected(sources, tmp_path, filename):
    run = capture_rule_coverage(sources[0], history_dir=sources[1], output_dir=tmp_path / "coverage")
    with (run / filename).open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): verify_rule_coverage(run)


@pytest.mark.parametrize("limit", ["MAX_SPECS", "MAX_COVERAGE_BYTES"])
def test_limits_fail_without_dropping_profiles_or_sources(sources, tmp_path, monkeypatch, limit):
    monkeypatch.setattr(coverage, limit, 0)
    with pytest.raises(ValueError): capture_rule_coverage(sources[0], history_dir=sources[1], output_dir=tmp_path / "coverage")
    run, = (tmp_path / "coverage").iterdir()
    assert not (run / "coverage.json").exists()


def test_size_limit_applies_to_stored_indented_json_not_only_compact_json(sources, tmp_path, monkeypatch):
    hypothetical = (tmp_path / "coverage" / ("0" * 32)).resolve()
    record = coverage._record(sources[0], sources[1], hypothetical)
    compact_size = len(coverage._canonical(record))
    stored_size = len(json.dumps(record, ensure_ascii=False, indent=2).encode("utf-8"))
    assert stored_size > compact_size + 1
    monkeypatch.setattr(coverage, "MAX_COVERAGE_BYTES", compact_size + 1)
    with pytest.raises(ValueError, match="recortarán"):
        capture_rule_coverage(sources[0], history_dir=sources[1], output_dir=tmp_path / "coverage")
    run, = (tmp_path / "coverage").iterdir()
    assert not (run / "coverage.json").exists()


def test_different_references_cannot_be_combined(sources, tmp_path, monkeypatch):
    actual = coverage.verify_compact_history
    def different(*args):
        record = deepcopy(actual(*args))
        record["reference"]["development_sha256"] = "f" * 64
        return record
    monkeypatch.setattr(coverage, "verify_compact_history", different)
    with pytest.raises(ValueError, match="referencia"):
        capture_rule_coverage(sources[0], history_dir=sources[1], output_dir=tmp_path / "coverage")


def test_cli_only_captures_or_verifies(sources, tmp_path, capsys):
    main(["capture", "--context-run", str(sources[0]), "--history-run", str(sources[1]), "--output-dir", str(tmp_path / "coverage")])
    main(["verify", "--run", capsys.readouterr().out.strip()])
    assert json.loads(capsys.readouterr().out)["strategy_selected"] is False
    with pytest.raises(SystemExit): main(["generate", "--context-run", str(sources[0])])
