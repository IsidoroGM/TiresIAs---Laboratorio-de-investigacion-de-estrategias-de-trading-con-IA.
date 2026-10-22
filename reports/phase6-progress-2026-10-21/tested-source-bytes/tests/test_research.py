"""Experimentos, controles y trazabilidad, con respuestas de IA simuladas."""

from copy import deepcopy
from datetime import date, timedelta
from decimal import Decimal, ROUND_DOWN, localcontext
from hashlib import sha256
import json

import pytest

from trading_ai.ai import ProviderError, ProviderReply
from trading_ai.experiments import (CRITERIA, ExperimentPolicy, expected_assessment,
                                    run_experiment, validate_assessment, validate_proposal)
from trading_ai.research import ResearchError, main, run_research


@pytest.fixture
def source(tmp_path):
    values = [3, 2, 1, 2, 3, 4, 3, 2, 1, 2, 3] * 4
    days = ''.join(f'<Cube time="{date(2025, 1, 1) + timedelta(days=i)}">'
                   f'<Cube currency="USD" rate="{price}"/></Cube>'
                   for i, price in enumerate(values))
    path = tmp_path / "ecb.xml"
    path.write_text('<Envelope xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">'
                    '<Cube>' + days + '</Cube></Envelope>', encoding="utf-8")
    return path


@pytest.fixture
def policy():
    return ExperimentPolicy(fast_window=2, slow_window=4)


@pytest.fixture
def proposal():
    return {"hypothesis": "Una EMA más rápida podría mejorar la rentabilidad sin aumentar el drawdown.",
            "criterion": CRITERIA[0], "tool": "run_experiment",
            "arguments": {"strategy": "ema", "fast_window": 1, "slow_window": 3}}


@pytest.mark.parametrize("field,value", [("cost_rate", "0"), ("initial_capital", "999999"),
                                         ("source", "other.xml"), ("pair", "BTC/USD"),
                                         ("allocation_fraction", "1"), ("code", "print(1)")])
def test_model_cannot_override_controls_or_execute_code(proposal, policy, field, value):
    proposal["arguments"][field] = value
    with pytest.raises(ValueError, match="no autorizados"):
        validate_proposal(proposal, policy)


@pytest.mark.parametrize("field,value", [("strategy", "eval"), ("fast_window", True),
                                         ("fast_window", 0), ("slow_window", 300),
                                         ("slow_window", 1)])
def test_model_parameters_are_bounded(proposal, policy, field, value):
    proposal["arguments"][field] = value
    with pytest.raises((ValueError, TypeError)):
        validate_proposal(proposal, policy)


def test_unknown_tool_and_identical_variant_rejected(proposal, policy):
    proposal["tool"] = "shell"
    with pytest.raises(ValueError, match="permitido"):
        validate_proposal(proposal, policy)
    proposal["tool"] = "run_experiment"
    proposal["arguments"] = {"strategy": "sma", "fast_window": 2, "slow_window": 4}
    with pytest.raises(ValueError, match="distinta"):
        validate_proposal(proposal, policy)


def test_experiment_preserves_data_and_records_common_assumptions(source, proposal, policy):
    original = source.read_bytes()
    result = run_experiment(source, proposal, policy)
    assert source.read_bytes() == original
    assert result["source"]["sha256"] == sha256(original).hexdigest()
    assert result["policy"]["cost_rate"] == "0.001"
    assert result["policy"]["allocation_fraction"] == "0.1"
    assert result["baseline"]["quote_currency"] == result["candidate"]["quote_currency"] == "USD"
    assert isinstance(result["candidate"]["final_equity"], str)
    assert result == run_experiment(source, deepcopy(proposal), policy)


@pytest.mark.parametrize("criterion,returns,drawdown,expected", [
    (CRITERIA[0], "2", "1", "supported_in_sample"),
    (CRITERIA[0], "2", "3", "not_supported_in_sample"),
    (CRITERIA[0], "0", "1", "not_supported_in_sample"),
    (CRITERIA[1], "1", "1", "supported_in_sample"),
    (CRITERIA[1], "0", "1", "not_supported_in_sample"),
    (CRITERIA[0], "1", "2", "inconclusive"),
])
def test_verdict_follows_predeclared_criterion_not_model_confidence(criterion, returns, drawdown, expected):
    result = {"proposal": {"criterion": criterion},
              "baseline": {"return_percent": "1", "max_drawdown_percent": "2", "closed_trades": 3},
              "candidate": {"return_percent": returns, "max_drawdown_percent": drawdown, "closed_trades": 3}}
    assert expected_assessment(result)["verdict"] == expected


def test_no_closed_trades_is_inconclusive(source, proposal):
    result = run_experiment(source, proposal)  # Base 20/60: muestra insuficiente.
    assert expected_assessment(result)["verdict"] == "inconclusive"


def test_invented_analysis_is_rejected(source, proposal, policy):
    result = run_experiment(source, proposal, policy)
    wrong = expected_assessment(result)
    wrong["return_comparison"] = "invented"
    with pytest.raises(ValueError, match="no coincide"):
        validate_assessment(wrong, result)


class ScriptedProvider:
    def __init__(self, answers):
        self.answers = iter(answers)
        self.calls = 0

    def describe(self):
        return {"provider": "ollama", "model": "test-local:4b", "model_digest": "a" * 64}

    def complete(self, messages, schema):
        self.calls += 1
        answer = next(self.answers)
        if isinstance(answer, Exception):
            raise answer
        return ProviderReply(answer if isinstance(answer, str) else json.dumps(answer),
                             "test-local:4b", {"input_tokens": 20, "output_tokens": 10, "api_cost_usd": "0"})


def events(directory):
    return [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]


def test_full_offline_research_logs_results_usage_and_rejects_automatic_winner(source, proposal, policy, tmp_path):
    measured = run_experiment(source, proposal, policy)
    provider = ScriptedProvider([proposal, expected_assessment(measured)])
    directory = run_research(provider, source=source, policy=policy, output_dir=tmp_path / "runs")
    assert provider.calls == 2
    recorded = events(directory)
    assert recorded[-1]["event"] == "run_completed"
    assert len(recorded[-1]["data"]["usage"]) == 2
    assert recorded[0]["data"]["engine_sha256"]["backtesting.py"]
    report = (directory / "report.md").read_text(encoding="utf-8")
    assert f"{Decimal(measured['candidate']['final_equity']):.6f}" in report
    assert "No hay validación fuera de muestra" in report
    assert "selección automática" in report
    assert "Origen de la conclusión: IA, verificada por Python." in report
    assert json.loads((directory / "analysis_origin.json").read_text(encoding="utf-8")) == {
        "source": "model", "verified_by": "python"}
    assert recorded[-1]["data"]["model_requests"] == 2


@pytest.mark.parametrize("base_windows,variant_slow,missing", [
    ((20, 60), 3, ["baseline"]),
    ((2, 4), 60, ["candidate"]),
    ((20, 60), 60, ["baseline", "candidate"]),
])
def test_zero_closures_produces_python_conclusion_without_model_analysis(
        source, proposal, tmp_path, base_windows, variant_slow, missing):
    policy = ExperimentPolicy(fast_window=base_windows[0], slow_window=base_windows[1])
    proposal["arguments"]["slow_window"] = variant_slow
    measured = run_experiment(source, proposal, policy)
    assert [name for name in ("baseline", "candidate") if measured[name]["closed_trades"] == 0] == missing

    class ProposalOnlyProvider(ScriptedProvider):
        def complete(self, messages, schema):
            if self.calls:
                pytest.fail("Con cero cierres no se debe pedir análisis al modelo.")
            return super().complete(messages, schema)

    provider = ProposalOnlyProvider([proposal])
    directory = run_research(provider, source=source, policy=policy, output_dir=tmp_path / "runs")
    assert provider.calls == 1
    assessment = json.loads((directory / "analysis.json").read_text(encoding="utf-8"))
    assert assessment == expected_assessment(measured)
    assert assessment["verdict"] == "inconclusive"
    origin = json.loads((directory / "analysis_origin.json").read_text(encoding="utf-8"))
    assert origin == {"source": "python", "reason": "no_closed_trades",
                      "strategies_without_closed_trades": missing}
    recorded = events(directory)
    precheck = next(item["data"] for item in recorded if item["event"] == "assessment_precheck")
    assert precheck["passed"] is False
    assert precheck["closed_trades"] == {name: measured[name]["closed_trades"] for name in ("baseline", "candidate")}
    assert not any(item["event"] == "model_request" and item["data"]["stage"] == "assessment" for item in recorded)
    assert recorded[-1]["event"] == "run_completed"
    assert recorded[-1]["data"]["analysis_origin"] == origin
    assert recorded[-1]["data"]["model_requests"] == 1
    assert len(recorded[-1]["data"]["usage"]) == 1
    assert recorded[-1]["data"]["usage"][0]["output_tokens"] == 10
    report = (directory / "report.md").read_text(encoding="utf-8")
    assert "Resultado inconcluso" in report
    assert "Origen de la conclusión: Python (control previo)." in report
    assert "El análisis estructurado de la IA coincide" not in report
    assert "sin operaciones cerradas" in report
    assert "Peticiones de IA: 1." in report
    assert f"{Decimal(measured['candidate']['final_equity']):.6f}" in report


def test_research_report_rounding_is_independent_of_callers_decimal_context(source, proposal, policy, tmp_path):
    measured = run_experiment(source, proposal, policy)
    expected_number = f"{Decimal(measured['candidate']['final_equity']):.6f}"
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_DOWN
        provider = ScriptedProvider([proposal, expected_assessment(measured)])
        directory = run_research(provider, source=source, policy=policy, output_dir=tmp_path)
    report = (directory / "report.md").read_text(encoding="utf-8")
    assert expected_number in report
    assert "Coste por compra o venta: 0.100 %" in report


@pytest.mark.parametrize("bad_answer", ['not JSON', {"tool": "shell"}])
def test_invalid_proposal_stops_before_tool_execution_and_keeps_usage(source, policy, tmp_path, bad_answer):
    provider = ScriptedProvider([bad_answer])
    with pytest.raises(ResearchError) as failure:
        run_research(provider, source=source, policy=policy, output_dir=tmp_path)
    recorded = events(failure.value.directory)
    assert provider.calls == 1
    assert not any(item["event"] == "tool_requested" for item in recorded)
    assert recorded[-1]["event"] == "run_failed"
    assert len(recorded[-1]["data"]["usage"]) == 1


def test_rejected_conclusion_keeps_engine_results_and_no_validated_report(source, proposal, policy, tmp_path):
    provider = ScriptedProvider([proposal, {"verdict": "always_better"}])
    with pytest.raises(ResearchError) as failure:
        run_research(provider, source=source, policy=policy, output_dir=tmp_path)
    directory = failure.value.directory
    assert (directory / "results.json").exists()
    assert not (directory / "report.md").exists()
    assert len(events(directory)[-1]["data"]["usage"]) == 2


def test_truncation_records_known_usage_and_never_retries(source, policy, tmp_path):
    provider = ScriptedProvider([ProviderError("truncated", {"output_tokens": 384})])
    with pytest.raises(ResearchError) as failure:
        run_research(provider, source=source, policy=policy, output_dir=tmp_path)
    assert provider.calls == 1
    assert events(failure.value.directory)[-1]["data"]["usage"][0]["output_tokens"] == 384


def test_repeated_runs_preserve_previous_files(source, proposal, policy, tmp_path):
    assessment = expected_assessment(run_experiment(source, proposal, policy))
    first = run_research(ScriptedProvider([proposal, assessment]), source=source, policy=policy, output_dir=tmp_path)
    original = (first / "events.jsonl").read_bytes()
    second = run_research(ScriptedProvider([proposal, assessment]), source=source, policy=policy, output_dir=tmp_path)
    assert first != second
    assert (first / "events.jsonl").read_bytes() == original


@pytest.mark.parametrize("cost,expected", [("0.01", "0.02"), (None, None), ("NaN", None)])
def test_provider_contract_keeps_future_costs_separate_from_local_zero(source, proposal, policy, tmp_path, cost, expected):
    class FutureProviderDouble(ScriptedProvider):
        def describe(self):
            return {"provider": "future_test_double", "model": "test-only"}

        def complete(self, messages, schema):
            reply = super().complete(messages, schema)
            return ProviderReply(reply.content, reply.model, {"api_cost_usd": cost})
    measured = run_experiment(source, proposal, policy)
    provider = FutureProviderDouble([proposal, expected_assessment(measured)])
    directory = run_research(provider, source=source, policy=policy, output_dir=tmp_path)
    assert events(directory)[-1]["data"]["api_cost_usd"] == expected
    if expected is None:
        assert "Coste de API registrado: no disponible" in (directory / "report.md").read_text(encoding="utf-8")


def test_openai_cli_fails_before_creating_research_run(tmp_path, capsys):
    with pytest.raises(SystemExit) as failure:
        main(["--provider", "openai", "--output-dir", str(tmp_path / "runs")])
    assert failure.value.code == 1
    assert "integración futura" in capsys.readouterr().err
    assert not (tmp_path / "runs").exists()
