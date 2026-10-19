"""Una reformulación estructurada por origen, con linaje externo y sin alterar las respuestas originales."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from trading_ai.ai import AIConfig, ResearchProvider, create_provider, load_ai_config
from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal, _api_cost
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.structured_ideas import _limits, propose_structured_idea
from trading_ai.structured_planning import _code_hashes as _planning_hashes, _review, _source


ACCESS_ROOT = ROOT / ".local/structured-revision-access"
MAX_CLAIMS = 128


class StructuredRevisionError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


def _code_hashes() -> dict:
    return {**_planning_hashes(), "structured_revision.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def _parent(directory: Path, frozen: Path):
    review, origin, proposal = _review(directory, frozen)
    if review["status"] != "needs_clarification":
        raise ValueError("Solo una revisión needs_clarification permite una reformulación estructurada.")
    claims = sorted(ACCESS_ROOT.glob("*.json"))
    if len(claims) > MAX_CLAIMS:
        raise ValueError("El historial de reformulaciones supera su límite explícito.")
    source = Path(proposal["run_dir"])
    for path in claims:
        claim = _strict_json(_read(path, 8192))
        if (not isinstance(claim, dict) or set(claim) != {"schema_version", "identity", "revision_run", "child_output_root", "state"}
                or type(claim["schema_version"]) is not int or claim["schema_version"] != 1
                or not Path(claim["revision_run"]).is_absolute()
                or Path(claim["child_output_root"]) != Path(claim["revision_run"]) / "i"
                or claim["state"] != "attempt_reserved_no_automatic_retry"):
            raise ValueError("Una reserva de reformulación está alterada o es incompatible.")
        if source.is_relative_to(Path(claim["child_output_root"])):
            raise ValueError("No se permiten cadenas: esta propuesta ya procede de una reformulación.")
    return review, origin, proposal


def _question(review: dict, proposal: dict) -> str:
    rules = {key: proposal["proposal"][key] for key in ("entry", "exit")}
    reason = review["reason"][:250]
    while True:
        context = {"task": "Reformular las reglas para resolver la duda; no afirmar equivalencia o mejora.",
                   "previous_rules": rules, "unverified_review_excerpt": reason,
                   "review_excerpt_truncated": len(reason) != len(review["reason"])}
        question = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
        if len(question) <= 800:
            return question
        if not reason:
            raise ValueError("Las reglas anteriores superan el contexto admitido para reformular.")
        reason = reason[:len(reason) // 2]


def _identity(review: dict) -> dict:
    return {"schema_version": 1, "proposal_sha256": review["source"]["sha256"]["proposal.json"],
            "development_sha256": review["reference"]["development_sha256"]}


def revise_structured_idea(provider: ResearchProvider, review_dir: str | Path, frozen_dir: str | Path, *,
                           config: AIConfig = AIConfig(), output_dir: str | Path = ROOT / ".local/structured-revisions") -> Path:
    _limits(config, "Reformulación estructurada")
    directory, frozen = Path(review_dir).resolve(), Path(frozen_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    child, claimed = None, False
    journal.record("structured_revision_started", parent_review=str(directory), max_new_model_requests=1, max_depth=1)
    try:
        review, origin, parent = _parent(directory, frozen)
        hashes = _code_hashes()
        question = _question(review, parent)
        identity = _identity(review)
        child_root = journal.directory / "i"
        claim = {"schema_version": 1, "identity": identity, "revision_run": str(journal.directory),
                 "child_output_root": str(child_root), "state": "attempt_reserved_no_automatic_retry"}
        ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
        access = ACCESS_ROOT / (sha256(_canonical(identity)).hexdigest() + ".json")
        if not access.exists() and len(list(ACCESS_ROOT.glob("*.json"))) >= MAX_CLAIMS:
            raise ValueError("El historial de reformulaciones ha alcanzado su límite explícito.")
        try:
            _write_exclusive(access, _canonical(claim))
        except FileExistsError as error:
            raise ValueError("Este origen ya tiene una reformulación reservada; no se repetirá.") from error
        claimed = True
        journal.save("lineage.json", {"parent_review": origin, "parent_source": review["source"], "question": question, "depth": 1})
        lineage_hash = sha256(_read(journal.directory / "lineage.json", 32768)).hexdigest()
        child = propose_structured_idea(provider, frozen, config=config, question=question, output_dir=child_root)
        revised, child_origin = _source(child, frozen)
        # _parent ignora la pregunta como permiso y sigue impidiendo cadenas mediante reservas de rutas.
        if (_parent(directory, frozen)[1] != origin or _code_hashes() != hashes
                or _read(access, 8192) != _canonical(claim)
                or sha256(_read(journal.directory / "lineage.json", 32768)).hexdigest() != lineage_hash):
            raise ValueError("El origen, el código o la reserva cambiaron durante la reformulación.")
        record = {"schema_version": 1, "protocol": "structured_revision_v1", "parent_review": origin,
                  "parent_source": review["source"], "reference": parent["reference"], "depth": 1,
                  "question": question, "child": child_origin, "status": revised["status"],
                  "lineage_sha256": lineage_hash,
                  "access": {"path": str(access), "sha256": sha256(_canonical(claim)).hexdigest()},
                  "new_model_requests": revised["model_requests"], "inherited_model_requests": parent["model_requests"],
                  "new_usage": revised["usage"], "inherited_usage": parent["usage"],
                  "new_api_cost_usd": revised["api_cost_usd"], "lineage_api_cost_usd": _api_cost(parent["usage"] + revised["usage"]),
                  "backtests": 0, "executable": False, "calculated_results": None, "code_sha256": hashes}
        _seal(journal, "revision.json", record, "structured_revision_completed")
    except Exception as error:
        journal.record("structured_revision_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       access_claimed=claimed, child_run=str(child or getattr(error, "directory", "")))
        raise StructuredRevisionError(str(error), journal.directory) from error
    return journal.directory


def verify_structured_revision(run_dir: str | Path, frozen_dir: str | Path) -> dict:
    directory, frozen = Path(run_dir).resolve(), Path(frozen_dir).resolve()
    record, _ = _artifact(directory, "revision.json", "structured_revision_completed")
    review, origin, parent = _parent(Path(record["parent_review"]["directory"]), frozen)
    child_dir = Path(record["child"]["directory"])
    if not child_dir.is_relative_to(directory / "i"):
        raise ValueError("La reformulación no pertenece a su carpeta de generación registrada.")
    child, child_origin = _source(child_dir, frozen)
    question = _question(review, parent)
    identity = _identity(review)
    access = ACCESS_ROOT / (sha256(_canonical(identity)).hexdigest() + ".json")
    access_raw = _read(access, 8192)
    expected_claim = {"schema_version": 1, "identity": identity, "revision_run": str(directory),
                      "child_output_root": str(directory / "i"), "state": "attempt_reserved_no_automatic_retry"}
    expected = {"schema_version": 1, "protocol": "structured_revision_v1", "parent_review": origin,
                "parent_source": review["source"], "reference": parent["reference"], "depth": 1, "question": question,
                "child": child_origin, "status": child["status"], "access": {"path": str(access), "sha256": sha256(access_raw).hexdigest()},
                "lineage_sha256": sha256(_read(directory / "lineage.json", 32768)).hexdigest(),
                "new_model_requests": child["model_requests"], "inherited_model_requests": parent["model_requests"],
                "new_usage": child["usage"], "inherited_usage": parent["usage"], "new_api_cost_usd": child["api_cost_usd"],
                "lineage_api_cost_usd": _api_cost(parent["usage"] + child["usage"]), "backtests": 0, "executable": False,
                "calculated_results": None, "code_sha256": _code_hashes()}
    if (_canonical(record) != _canonical(expected) or child["question"] != question
            or _strict_json(access_raw) != expected_claim
            or _strict_json(_read(directory / "lineage.json", 32768)) != {
                "parent_review": origin, "parent_source": review["source"], "question": question, "depth": 1}):
        raise ValueError("El linaje, las reglas, el consumo o las fuentes de reformulación han cambiado.")
    return record


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — una reformulación estructurada vinculada a revisión")
    parser.add_argument("command", choices=("revise", "verify"))
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--frozen-run", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output-dir", type=Path, default=ROOT / ".local/structured-revisions")
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            record = verify_structured_revision(args.run, args.frozen_run)
            print(json.dumps({"status": record["status"], "new_model_requests": record["new_model_requests"], "executable": False}))
            return
        config = load_ai_config(args.config)
        _limits(config, "Reformulación estructurada")
        directory = revise_structured_idea(create_provider(config), args.run, args.frozen_run, config=config, output_dir=args.output_dir)
    except StructuredRevisionError as error:
        parser.exit(1, f"Reformulación detenida: {error}. Evidencia: {error.directory}\n")
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Reformulación no verificable: {error}\n")
    print(f"Registro: {directory}")


if __name__ == "__main__":
    main()
