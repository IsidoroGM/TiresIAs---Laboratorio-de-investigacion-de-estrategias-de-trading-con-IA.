"""Registro previo a evaluación: trazabilidad, rechazos y ausencia de métricas futuras."""

from datetime import date, timedelta
from hashlib import sha256
import json
from pathlib import Path

import pytest

from trading_ai.ai import ProviderReply
from trading_ai.experiments import CRITERIA, ExperimentPolicy, expected_assessment, run_experiment
from trading_ai.holdout import freeze_proposal, main, verify_frozen_proposal
from trading_ai.research import run_research
from trading_ai.validation import prepare_validation_split


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def setup(tmp_path):
    source = tmp_path / "source.xml"
    values = [3, 2, 1, 2, 3, 4, 3, 2, 1, 2, 3] * 4
    days = ''.join(f'<Cube time="{date(2025, 1, 1) + timedelta(days=index)}">'
                   + ''.join(f'<Cube currency="{currency}" rate="{value * factor}"/>'
                             for currency, factor in (("USD", 1), ("GBP", 2), ("JPY", 100), ("CHF", 3)))
                   + '</Cube>' for index, value in enumerate(values))
    source.write_text('<Envelope xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">'
                      '<Cube>' + days + '</Cube></Envelope>', encoding="utf-8")
    split = prepare_validation_split(source, date(2025, 1, 23), tmp_path / "splits")
    policy = ExperimentPolicy(fast_window=2, slow_window=4)
    proposal = {"hypothesis": "Probar una EMA más rápida.", "criterion": CRITERIA[0],
                "tool": "run_experiment", "arguments": {"strategy": "ema", "fast_window": 1, "slow_window": 3}}
    class Provider:
        def __init__(self, result):
            self.answers = iter([proposal, expected_assessment(result)])
        def describe(self):
            return {"provider": "test", "model": "offline"}
        def complete(self, messages, schema):
            return ProviderReply(json.dumps(next(self.answers)), "offline", {"api_cost_usd": "0"})
    def research_for(path):
        result = run_experiment(path, proposal, policy)
        return run_research(Provider(result), source=path, policy=policy, output_dir=tmp_path / "research")
    research = research_for(split / "development.xml")
    return split, research, research_for


def test_freeze_and_verify_never_calculate_evaluation_and_preserve_references(setup, tmp_path, monkeypatch):
    split, research, _ = setup
    before = {path: path.read_bytes() for directory in (split, research) for path in directory.iterdir()}
    import trading_ai.holdout as holdout
    actual = holdout.run_experiment
    calls = []
    def development_only(source, *args, **kwargs):
        assert Path(source) == split / "development.xml"
        calls.append(source)
        return actual(source, *args, **kwargs)
    monkeypatch.setattr(holdout, "run_experiment", development_only)
    directory = freeze_proposal(split, research, tmp_path / "frozen")
    frozen = verify_frozen_proposal(directory)
    result = read_json(research / "results.json")
    assert frozen["proposal"] == result["proposal"]
    assert frozen["policy"] == result["policy"]
    assert frozen["development_result"] == result
    assert frozen["stage"] == "frozen_not_evaluated"
    assert frozen["split"]["manifest_sha256"] == sha256((split / "manifest.json").read_bytes()).hexdigest()
    assert len(calls) == 2
    assert all(path.read_bytes() == raw for path, raw in before.items())
    assert "evaluation_result" not in frozen


@pytest.mark.parametrize("source_name", ["evaluation.xml", "original"])
def test_cannot_freeze_research_on_evaluation_or_full_history(setup, tmp_path, source_name):
    split, _, research_for = setup
    source = split / source_name if source_name != "original" else tmp_path / "source.xml"
    wrong = research_for(source)
    with pytest.raises(ValueError, match="desarrollo"):
        freeze_proposal(split, wrong, tmp_path / "frozen")
    directory, = (tmp_path / "frozen").iterdir()
    events = [json.loads(line) for line in (directory / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert events[-1]["event"] == "freeze_failed"
    assert not (directory / "frozen.json").exists()


def test_incomplete_research_cannot_be_frozen(setup, tmp_path):
    split, research, _ = setup
    events = (research / "events.jsonl").read_text(encoding="utf-8").splitlines()
    (research / "events.jsonl").write_text('\n'.join(events[:-1]) + '\n', encoding="utf-8")
    with pytest.raises(ValueError, match="terminado"):
        freeze_proposal(split, research, tmp_path / "frozen")


def test_invented_development_result_rejected_before_registration(setup, tmp_path):
    split, research, _ = setup
    result = read_json(research / "results.json")
    result["candidate"]["final_equity"] = "9999999"
    write_json(research / "results.json", result)
    with pytest.raises(ValueError, match="no coinciden con el motor"):
        freeze_proposal(split, research, tmp_path / "frozen")


@pytest.mark.parametrize("target", ["proposal", "criterion", "policy", "development_result"])
def test_frozen_proposal_or_controls_cannot_be_edited(setup, tmp_path, target):
    split, research, _ = setup
    directory = freeze_proposal(split, research, tmp_path / "frozen")
    frozen = read_json(directory / "frozen.json")
    if target == "proposal":
        frozen["proposal"]["arguments"]["fast_window"] = 2
    elif target == "criterion":
        frozen["proposal"]["criterion"] = CRITERIA[1]
    elif target == "policy":
        frozen["policy"]["cost_rate"] = "0"
    else:
        frozen["development_result"]["candidate"]["return_percent"] = "100"
    write_json(directory / "frozen.json", frozen)
    with pytest.raises(ValueError, match="SHA-256"):
        verify_frozen_proposal(directory)


@pytest.mark.parametrize("target", ["development.xml", "evaluation.xml", "manifest.json", "results.json",
                                     "analysis.json", "analysis_origin.json", "events.jsonl"])
def test_changed_data_manifest_or_research_invalidates_registration(setup, tmp_path, target):
    split, research, _ = setup
    directory = freeze_proposal(split, research, tmp_path / "frozen")
    path = (split if target in ("development.xml", "evaluation.xml", "manifest.json") else research) / target
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="Integridad|ha cambiado"):
        verify_frozen_proposal(directory)


def test_code_change_invalidates_registration(setup, tmp_path, monkeypatch):
    split, research, _ = setup
    directory = freeze_proposal(split, research, tmp_path / "frozen")
    monkeypatch.setattr("trading_ai.holdout._code_hashes", lambda: {"backtesting.py": "changed"})
    with pytest.raises(ValueError, match="código"):
        verify_frozen_proposal(directory)


def test_incomplete_seal_or_modified_checksum_is_rejected(setup, tmp_path):
    split, research, _ = setup
    directory = freeze_proposal(split, research, tmp_path / "frozen")
    (directory / "events.jsonl").write_text('', encoding="utf-8")
    with pytest.raises(ValueError, match="registro completo"):
        verify_frozen_proposal(directory)
    (directory / "frozen.sha256").write_text('0' * 64, encoding="ascii")
    with pytest.raises(ValueError, match="SHA-256"):
        verify_frozen_proposal(directory)


def test_no_overwrite_when_freezing_again(setup, tmp_path):
    split, research, _ = setup
    first = freeze_proposal(split, research, tmp_path / "frozen")
    original = {p.name: p.read_bytes() for p in first.iterdir()}
    second = freeze_proposal(split, research, tmp_path / "frozen")
    assert first != second
    assert {p.name: p.read_bytes() for p in first.iterdir()} == original
    assert verify_frozen_proposal(second)["proposal"] == read_json(first / "frozen.json")["proposal"]


@pytest.mark.parametrize("field,value", [("cost_rate", "invalid"), ("initial_capital", "NaN"),
                                         ("allocation_fraction", "2"), ("cost_rate", 0)])
def test_invalid_policy_in_research_cannot_be_registered(setup, tmp_path, field, value):
    split, research, _ = setup
    result = read_json(research / "results.json")
    result["policy"][field] = value
    write_json(research / "results.json", result)
    with pytest.raises(ValueError):
        freeze_proposal(split, research, tmp_path / "frozen")


def test_manifest_cannot_redirect_partition_paths(setup, tmp_path):
    split, research, _ = setup
    plan = read_json(split / "manifest.json")
    plan["partitions"]["development"]["file"] = "../source.xml"
    write_json(split / "manifest.json", plan)
    with pytest.raises(ValueError, match="Nombre de partición"):
        freeze_proposal(split, research, tmp_path / "frozen")


def test_cli_freezes_and_verifies_without_ai(setup, tmp_path, monkeypatch, capsys):
    split, research, _ = setup
    monkeypatch.setattr("trading_ai.ai.create_provider", lambda *args: pytest.fail("Sin IA"))
    main(["freeze", "--split", str(split), "--research-run", str(research), "--output-dir", str(tmp_path / "frozen")])
    directory, = (tmp_path / "frozen").iterdir()
    main(["verify", "--frozen-run", str(directory)])
    assert "evaluación no ejecutada" in capsys.readouterr().out


def test_cli_rejects_missing_registration(tmp_path, capsys):
    with pytest.raises(SystemExit) as failure:
        main(["verify", "--frozen-run", str(tmp_path / "missing")])
    assert failure.value.code == 1
    assert "Registro detenido" in capsys.readouterr().err
