"""Descripciones completas del contrato, con prosa original intacta y sin inferir intención."""

from copy import deepcopy
from pathlib import Path

import pytest

from test_discovery import Provider, read_json, registered
from test_holdout import setup
from test_structured_ideas import generated, proposal
from trading_ai.structured_brief import create_structured_brief, describe_proposal, main, verify_structured_brief
from trading_ai.structured_ideas import propose_structured_idea


@pytest.fixture(autouse=True)
def isolated_history(tmp_path, monkeypatch):
    monkeypatch.setattr("trading_ai.idea_memory.MEMORY_ROOT", tmp_path / "memory")
    monkeypatch.setattr("trading_ai.structured_ideas.ACCESS_ROOT", tmp_path / "ideas-access")


@pytest.mark.parametrize("operator,phrase", [("gt","es mayor que"),("gte","es mayor o igual que"),("lt","es menor que"),
                                         ("lte","es menor o igual que"),("eq","es igual a"),
                                         ("crosses_above","cruza por encima de"),("crosses_below","cruza por debajo de")])
def test_strict_inclusive_and_crossing_operators_keep_their_meaning(proposal, operator, phrase):
    proposal["entry"]["operator"] = operator
    description = describe_proposal(proposal)
    assert description["entry"] == f"Entrar largo cuando la referencia actual {phrase} el valor 1."
    assert description["origin"] == "python_from_validated_rules"


@pytest.mark.parametrize("kind,label", [("sma","la SMA"),("ema","la EMA"),("rolling_min","el mínimo móvil"),
                                      ("rolling_max","el máximo móvil")])
def test_indicator_windows_and_past_lags_are_explicit(proposal, kind, label):
    proposal["entry"]["left"] = {"kind":kind,"window":252,"lag":252}
    description = describe_proposal(proposal)
    assert f"{label} de 252 observaciones de hace 252 observaciones" in description["entry"]
    assert description["entry"].endswith(".") and "observación siguiente, si existe" in description["execution"]


def test_singular_observation_does_not_become_a_day_or_a_second_execution_delay(proposal):
    proposal["exit"]["left"] = {"kind":"reference","lag":1}
    proposal["exit"]["right"] = {"kind":"ema","window":1,"lag":0}
    description = describe_proposal(proposal)
    assert "la referencia de hace 1 observación" in description["exit"]
    assert "la EMA actual de 1 observación" in description["exit"]
    assert "día" not in description["exit"]


def test_incomplete_model_text_is_preserved_while_rule_description_is_complete(registered, proposal, tmp_path):
    _, frozen = registered
    proposal["title"] = "Título y re"
    proposal["hypothesis"] = "La salida ocurre por debajo de la"
    original = deepcopy(proposal)
    source = propose_structured_idea(Provider(proposal), frozen, output_dir=tmp_path / "source")
    before = {path:path.read_bytes() for path in source.iterdir()}
    brief = create_structured_brief(source, frozen, output_dir=tmp_path / "briefs")
    record = verify_structured_brief(brief, frozen)
    assert record["model_description"] == {"origin":"model_unverified","title":proposal["title"],"hypothesis":proposal["hypothesis"]}
    assert record["rule_description"]["exit"] == "Salir de la posición larga cuando la referencia actual es menor o igual que el valor 1."
    assert record["executable"] is False and record["calculated_results"] is None
    assert record["model_requests"] == 0 and record["api_cost_usd"] == "0"
    assert proposal == original and all(path.read_bytes()==raw for path,raw in before.items())


def test_creation_and_verification_do_not_generate_signals_use_model_or_open_outer_data(generated, tmp_path, monkeypatch):
    _, frozen, source, _ = generated
    for name in ("trading_ai.rules.RuleStrategy.generate_signals","trading_ai.experiments.run_backtest","trading_ai.ai.create_provider"):
        monkeypatch.setattr(name,lambda *a,**k:pytest.fail("Solo describir campos verificados"))
    actual_open = Path.open
    def guarded(path,*a,**k):
        assert path.name not in ("evaluation.xml","comparison.json")
        return actual_open(path,*a,**k)
    monkeypatch.setattr(Path,"open",guarded)
    brief = create_structured_brief(source,frozen,output_dir=tmp_path/"briefs")
    assert verify_structured_brief(brief,frozen)["status"] == "review_aid_only"


@pytest.mark.parametrize("filename",["brief.json","report.md","events.jsonl"])
def test_changed_artifacts_cannot_be_verified(generated,tmp_path,filename):
    _,frozen,source,_ = generated
    brief = create_structured_brief(source,frozen,output_dir=tmp_path/"briefs")
    with (brief/filename).open("ab") as stream:stream.write(b' ')
    with pytest.raises(ValueError):verify_structured_brief(brief,frozen)


def test_raw_markdown_is_presented_as_literal_text_without_changing_it(registered,proposal,tmp_path):
    _,frozen=registered
    proposal["hypothesis"]="```\n# Texto del modelo sin verificar"
    source=propose_structured_idea(Provider(proposal),frozen,output_dir=tmp_path/"source")
    brief=create_structured_brief(source,frozen,output_dir=tmp_path/"briefs")
    report=(brief/"report.md").read_text(encoding="utf-8")
    assert "    ```\n    # Texto del modelo sin verificar" in report
    assert verify_structured_brief(brief,frozen)["model_description"]["hypothesis"]==proposal["hypothesis"]
