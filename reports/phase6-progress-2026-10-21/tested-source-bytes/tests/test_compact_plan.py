"""Plan previo sin cálculo ni cambios de riesgo, ligado al objetivo congelado."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from test_compact_candidate import isolated_history, prepared_request, transport
from test_compact_review import isolated_reviews, candidate, assessment
from test_discovery import registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from test_structured_session import session
from test_structured_draft_request import memory
from trading_ai.compact_plan import CompactPlanError, main, prepare_compact_plan, verify_compact_plan
from trading_ai.compact_review import SOURCE_FILES, review_compact_candidate
from trading_ai.research_session import _origin
from trading_ai.rule_planning import _canonical
from trading_ai import rule_execution as execution


@pytest.fixture
def reviewed(candidate, tmp_path):
    run, record = candidate
    review = review_compact_candidate(run, assessment(record, _origin(run, SOURCE_FILES)), output_dir=tmp_path / "reviews")
    return review, record


def test_frozen_controls_exact_rules_and_data_are_kept_without_calculation(reviewed, tmp_path, monkeypatch):
    review, candidate = reviewed
    def forbidden(*args, **kwargs): pytest.fail("Preparar no puede calcular, evaluar o consultar")
    for name in ("trading_ai.compact_ollama.CompactOllamaProvider.complete", "trading_ai.experiments.run_backtest",
                 "trading_ai.rules.RuleStrategy.generate_signals", "trading_ai.backtesting.run_backtest", "socket.socket.connect"):
        monkeypatch.setattr(name, forbidden)
    run = prepare_compact_plan(review, output_dir=tmp_path / "plans")
    plan = verify_compact_plan(run)
    frozen = json.loads((Path(candidate["reference"]["frozen_dir"]) / "frozen.json").read_bytes())
    assert plan["policy"] == frozen["policy"] and plan["criterion"] == frozen["proposal"]["criterion"]
    assert plan["candidate"] == {"spec": candidate["spec"], "spec_sha256": candidate["spec_sha256"]}
    assert plan["data"]["sha256"] == sha256((run / "development.xml").read_bytes()).hexdigest()
    assert plan["budget"]["candidate_backtests"] == plan["budget"]["baseline_backtests"] == 1
    assert plan["new_usage"]["backtests"] == plan["new_usage"]["model_requests"] == 0
    assert plan["executable"] is plan["outer_evaluation_allowed"] is False
    assert plan["calculated_results"] is None and plan["execution_requires_explicit_tool"] is True
    assert not execution.ACCESS_ROOT.exists()


@pytest.mark.parametrize("decision", ["rejected", "needs_clarification"])
def test_unaccepted_reviews_cannot_create_plans(candidate, tmp_path, decision):
    run, record = candidate
    review = review_compact_candidate(run, assessment(record, _origin(run, SOURCE_FILES), decision), output_dir=tmp_path / "reviews")
    with pytest.raises(CompactPlanError, match="aceptada"): prepare_compact_plan(review, output_dir=tmp_path / "plans")


def test_existing_calculation_cannot_be_reopened_by_new_contract(reviewed, tmp_path):
    review, _ = reviewed
    run = prepare_compact_plan(review, output_dir=tmp_path / "plans")
    plan = verify_compact_plan(run)
    identity = execution._identity(plan)
    assert plan["calculation_id"] == sha256(_canonical(identity)).hexdigest()
    renamed = deepcopy(plan)
    renamed["candidate"]["spec"]["name"] = "another_name"
    renamed["criterion"] = "different criterion does not change calculations"
    assert execution._identity(renamed) == identity
    execution.ACCESS_ROOT.mkdir(parents=True)
    (execution.ACCESS_ROOT / (plan["calculation_id"] + ".json")).write_bytes(b'{}')
    # El plan ya registrado sigue siendo verificable; no vuelve a liberar el cálculo.
    assert verify_compact_plan(run) == plan
    with pytest.raises(CompactPlanError, match="reservado"): prepare_compact_plan(review, output_dir=tmp_path / "second-plans")


@pytest.mark.parametrize("filename", ["plan.json", "plan.json.sha256", "events.jsonl", "development.xml"])
def test_plan_tampering_is_detected(reviewed, tmp_path, filename):
    run = prepare_compact_plan(reviewed[0], output_dir=tmp_path / "plans")
    with (run / filename).open("ab") as stream: stream.write(b' changed')
    with pytest.raises(ValueError): verify_compact_plan(run)


def test_cli_only_prepares_or_reads_and_cannot_execute(reviewed, tmp_path, capsys):
    main(["prepare", "--review-run", str(reviewed[0]), "--output-dir", str(tmp_path / "plans")])
    run = capsys.readouterr().out.strip()
    main(["verify", "--run", run])
    assert json.loads(capsys.readouterr().out)["new_usage"]["backtests"] == 0
    with pytest.raises(SystemExit): main(["execute", "--run", run])
