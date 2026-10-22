"""Separación temporal, conservación de datos y ausencia de acceso futuro al desarrollar."""

from copy import deepcopy
from datetime import date, datetime, timedelta
from hashlib import sha256
import json
import xml.etree.ElementTree as ET

import pytest

from trading_ai.ai import ProviderReply
from trading_ai.data import SUPPORTED_PAIRS, load_ecb_rates
from trading_ai.experiments import CRITERIA, ExperimentPolicy, expected_assessment, run_experiment
from trading_ai.research import run_research
from trading_ai.validation import NAMESPACE, main, prepare_validation_split


def write_source(path, *, future_multiplier=1, reverse=False):
    root = ET.Element(f"{{{NAMESPACE}}}Envelope")
    container = ET.SubElement(root, f"{{{NAMESPACE}}}Cube")
    values = [3, 2, 1, 2, 3, 4, 3, 2, 1, 2, 3] * 4
    rows = list(enumerate(values))
    if reverse:
        rows.reverse()
    for index, value in rows:
        day = ET.SubElement(container, f"{{{NAMESPACE}}}Cube",
                            time=str(date(2025, 1, 1) + timedelta(days=index)))
        for currency, factor in (("USD", 1), ("GBP", 2), ("JPY", 100), ("CHF", 3)):
            adjusted = value * (future_multiplier if index >= 22 else 1)
            ET.SubElement(day, f"{{{NAMESPACE}}}Cube", currency=currency, rate=str(adjusted * factor))
    path.write_bytes(ET.tostring(root, encoding="utf-8"))
    return path


@pytest.fixture
def source(tmp_path):
    return write_source(tmp_path / "source.xml", reverse=True)


def manifest(directory):
    return json.loads((directory / "manifest.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("pair", SUPPORTED_PAIRS)
def test_split_preserves_exact_rates_without_overlap_or_missing_days(source, tmp_path, pair):
    original = source.read_bytes()
    cutoff = date(2025, 1, 23)
    directory = prepare_validation_split(source, cutoff, tmp_path / "runs")
    development = load_ecb_rates(directory / "development.xml", pair)
    evaluation = load_ecb_rates(directory / "evaluation.xml", pair)
    assert development + evaluation == load_ecb_rates(source, pair)
    assert all(day < cutoff for day, _ in development)
    assert all(day >= cutoff for day, _ in evaluation)
    assert evaluation[0][0] == cutoff
    assert set(day for day, _ in development).isdisjoint(day for day, _ in evaluation)
    assert source.read_bytes() == original


def test_manifest_links_bytes_to_source_boundary_and_account_policy(source, tmp_path):
    directory = prepare_validation_split(source, date(2025, 1, 23), tmp_path / "runs")
    plan = manifest(directory)
    assert plan["stage"] == "prepared_not_evaluated"
    assert plan["source"]["sha256"] == sha256(source.read_bytes()).hexdigest()
    assert plan["source"]["observations"] == 44
    assert plan["cutoff"] == "2025-01-23"
    assert plan["execution_policy"] == {
        "accounts": "independent_per_partition_and_pair", "carry_positions": False,
        "carry_signals": False, "indicator_warmup": "inside_each_partition"}
    for name, metadata in plan["partitions"].items():
        content = (directory / metadata["file"]).read_bytes()
        assert metadata["sha256"] == sha256(content).hexdigest()
        rates = load_ecb_rates(directory / metadata["file"], "EUR/USD")
        assert metadata["observations"] == len(rates) == 22
        assert metadata["first_date"] == str(rates[0][0])
        assert metadata["last_date"] == str(rates[-1][0])


def test_cutoff_in_a_calendar_gap_assigns_next_observation_to_evaluation(source, tmp_path):
    tree = ET.parse(source)
    container = tree.getroot().find(f"{{{NAMESPACE}}}Cube")
    for child in list(container):
        if child.attrib["time"] == "2025-01-23":
            container.remove(child)
    tree.write(source, encoding="utf-8")
    plan = manifest(prepare_validation_split(source, date(2025, 1, 23), tmp_path / "runs"))
    assert plan["partitions"]["development"]["last_date"] == "2025-01-22"
    assert plan["partitions"]["evaluation"]["first_date"] == "2025-01-24"


@pytest.mark.parametrize("cutoff", [date(2025, 1, 1), date(2030, 1, 1), "2025-01-23",
                                     datetime(2025, 1, 23), None])
def test_invalid_boundary_fails_before_writing(source, tmp_path, cutoff):
    with pytest.raises(ValueError):
        prepare_validation_split(source, cutoff, tmp_path / "runs")
    assert not (tmp_path / "runs").exists()


@pytest.mark.parametrize("damage", ["duplicate", "missing_chf", "negative", "invalid_date", "malformed"])
def test_invalid_source_rejected_before_writing(source, tmp_path, damage):
    tree = ET.parse(source)
    container = tree.getroot().find(f"{{{NAMESPACE}}}Cube")
    day = list(container)[0]
    if damage == "duplicate":
        container.append(deepcopy(day))
    elif damage == "missing_chf":
        day.remove(day.find(f"{{{NAMESPACE}}}Cube[@currency='CHF']"))
    elif damage == "negative":
        day.find(f"{{{NAMESPACE}}}Cube[@currency='USD']").set("rate", "-1")
    elif damage == "invalid_date":
        day.set("time", "2025-13-01")
    tree.write(source, encoding="utf-8")
    if damage == "malformed":
        source.write_text("<invalid", encoding="utf-8")
    with pytest.raises(ValueError):
        prepare_validation_split(source, date(2025, 1, 23), tmp_path / "runs")
    assert not (tmp_path / "runs").exists()


def test_source_change_during_loading_is_detected(source, tmp_path, monkeypatch):
    import trading_ai.validation as validation
    reader = validation.load_ecb_rates
    def changing_reader(path, pair):
        rates = reader(path, pair)
        if pair == "USD/CHF":
            source.write_bytes(source.read_bytes() + b"\n")
        return rates
    monkeypatch.setattr(validation, "load_ecb_rates", changing_reader)
    with pytest.raises(ValueError, match="cambiaron"):
        prepare_validation_split(source, date(2025, 1, 23), tmp_path / "runs")
    assert not (tmp_path / "runs").exists()


def test_repeated_preparations_keep_previous_files_and_same_partitions(source, tmp_path):
    first = prepare_validation_split(source, date(2025, 1, 23), tmp_path / "runs")
    saved = {p.name: p.read_bytes() for p in first.iterdir()}
    second = prepare_validation_split(source, date(2025, 1, 23), tmp_path / "runs")
    assert first != second
    assert {p.name: p.read_bytes() for p in first.iterdir()} == saved
    assert {p.name: p.read_bytes() for p in second.iterdir()} == saved


def test_future_prices_cannot_change_development_or_its_research_messages(tmp_path):
    policy = ExperimentPolicy(fast_window=2, slow_window=4)
    proposal = {"hypothesis": "Probar una EMA más rápida.", "criterion": CRITERIA[0],
                "tool": "run_experiment", "arguments": {"strategy": "ema", "fast_window": 1, "slow_window": 3}}
    class DevelopmentProvider:
        def __init__(self, assessment):
            self.answers = iter([proposal, assessment])
            self.messages = []
        def describe(self):
            return {"provider": "test", "model": "offline"}
        def complete(self, messages, schema):
            self.messages.append(deepcopy(messages))
            return ProviderReply(json.dumps(next(self.answers)), "offline", {"api_cost_usd": "0"})
    runs = []
    for multiplier in (1, 100):
        source = write_source(tmp_path / f"source-{multiplier}.xml", future_multiplier=multiplier)
        directory = prepare_validation_split(source, date(2025, 1, 23), tmp_path / "splits")
        development = directory / "development.xml"
        measured = run_experiment(development, proposal, policy)
        provider = DevelopmentProvider(expected_assessment(measured))
        research = run_research(provider, source=development, policy=policy, output_dir=tmp_path / "research")
        # El identificador del experimento es distinto en cada ejecución; no es un dato de mercado.
        for messages in provider.messages:
            for message in messages:
                try:
                    result = json.loads(message["content"])
                except json.JSONDecodeError:
                    continue
                if isinstance(result, dict):
                    result.pop("experiment_id", None)
                    message["content"] = json.dumps(result)
        assert (research / "report.md").exists()
        runs.append((directory, measured, provider.messages))
    assert (runs[0][0] / "development.xml").read_bytes() == (runs[1][0] / "development.xml").read_bytes()
    assert (runs[0][0] / "evaluation.xml").read_bytes() != (runs[1][0] / "evaluation.xml").read_bytes()
    assert runs[0][1:] == runs[1][1:]


@pytest.mark.parametrize("cutoff", ["20250123", "2025-1-23", "2025-02-30", "bad"])
def test_cli_requires_explicit_iso_date(source, tmp_path, cutoff):
    with pytest.raises(SystemExit) as failure:
        main(["--data", str(source), "--cutoff", cutoff, "--output-dir", str(tmp_path / "runs")])
    assert failure.value.code == 2
    assert not (tmp_path / "runs").exists()


def test_cli_prepares_only_without_model_or_backtest(source, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr("trading_ai.ai.create_provider", lambda *args: pytest.fail("Sin IA"))
    monkeypatch.setattr("trading_ai.experiments.run_backtest", lambda *args, **kwargs: pytest.fail("Sin evaluación"))
    main(["--data", str(source), "--cutoff", "2025-01-23", "--output-dir", str(tmp_path / "runs")])
    assert "Sin evaluar estrategias ni consultar IA" in capsys.readouterr().out
    directory, = (tmp_path / "runs").iterdir()
    assert {p.name for p in directory.iterdir()} == {"development.xml", "evaluation.xml", "manifest.json"}
