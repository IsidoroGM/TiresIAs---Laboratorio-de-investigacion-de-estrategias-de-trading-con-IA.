"""Sesión desde una propuesta verificada: consumo heredado, revisión separada y ejecución acotada."""

import argparse
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _claim_action, _inside, _origin, _save_stage, _stage
from trading_ai.robustness import _development
from trading_ai.rule_planning import _canonical
from trading_ai.structured_execution import (_code_hashes as _execution_hashes, execute_structured_plan,
                                            verify_structured_execution)
from trading_ai.structured_planning import (_source, prepare_structured_plan, review_structured_idea,
                                           validate_assessment, verify_structured_review)


ACCESS_ROOT = ROOT / ".local/structured-session-access"
BUDGET = {"source_model_requests": 1, "new_model_requests": 0, "backtests": 2,
          "parameter_variations": 0, "automatic_retries": 0}


class StructuredSessionError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


def _code_hashes() -> dict:
    return {**_execution_hashes(), **{name: sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                                    for name in ("research_session.py", "agent_feedback.py", "structured_session.py")}}


def _identity(origin: dict, reference: dict) -> dict:
    return {"schema_version": 1, "reference": reference, "proposal_sha256": origin["sha256"]["proposal.json"]}


def _manifest(directory: Path, origin: dict, proposal: dict, reference: dict) -> dict:
    if proposal["status"] != "pending_semantic_review":
        raise ValueError("La sesión requiere una propuesta estructurada pendiente, no una duplicada.")
    return {"schema_version": 1, "protocol": "structured_session_v1", "session_dir": str(directory),
            "source": origin, "reference": reference, "budget": deepcopy(BUDGET),
            "technical_review_required": True, "scope": "known_development_history_only",
            "outer_evaluation_allowed": False, "code_sha256": _code_hashes()}


def create_structured_session(proposal_dir: str | Path, frozen_dir: str | Path, *,
                              output_dir: str | Path = ROOT / ".local/structured-sessions") -> Path:
    source, frozen = Path(proposal_dir).resolve(), Path(frozen_dir).resolve()
    proposal, origin = _source(source, frozen)
    _, reference, _ = _development(frozen)
    if proposal["status"] != "pending_semantic_review":
        raise ValueError("Una propuesta duplicada no puede iniciar otra sesión.")
    journal = RunJournal(Path(output_dir).resolve())
    try:
        identity = _identity(origin, reference)
        ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
        claim = {"schema_version": 1, "identity": identity, "session_dir": str(journal.directory)}
        access_path = ACCESS_ROOT / (sha256(_canonical(identity)).hexdigest() + ".json")
        try:
            _write_exclusive(access_path, _canonical(claim))
        except FileExistsError as error:
            raise ValueError("Esta propuesta ya tiene una sesión registrada; no se reiniciará.") from error
        manifest = _manifest(journal.directory, origin, proposal, reference)
        journal.save("session.json", manifest)
        checksum = sha256((journal.directory / "session.json").read_bytes()).hexdigest()
        _write_exclusive(journal.directory / "session.sha256", (checksum + "\n").encode("ascii"))
        if _source(source, frozen)[1] != origin or manifest["code_sha256"] != _code_hashes():
            raise ValueError("El origen o el código cambiaron durante la preparación de sesión.")
        journal.record("structured_session_prepared", session_sha256=checksum, access_sha256=sha256(_canonical(claim)).hexdigest(),
                       budget=BUDGET, source_model_requests=1, new_model_requests=0, new_api_cost_usd="0")
    except Exception as error:
        journal.record("structured_session_preparation_failed", message=str(error)[:1000], new_model_requests=0, new_api_cost_usd="0")
        raise StructuredSessionError(str(error), journal.directory) from error
    return journal.directory


def _load(directory: Path) -> tuple[dict, dict]:
    raw = _read(directory / "session.json", 65536)
    manifest = _strict_json(raw)
    checksum = sha256(raw).hexdigest()
    frozen = Path(manifest["reference"]["frozen_dir"])
    proposal, origin = _source(Path(manifest["source"]["directory"]), frozen)
    _, reference, _ = _development(frozen)
    events = [_strict_json(line) for line in _read(directory / "events.jsonl", 65536).splitlines()]
    expected = _manifest(directory, origin, proposal, reference)
    identity = _identity(origin, reference)
    claim_raw = _read(ACCESS_ROOT / (sha256(_canonical(identity)).hexdigest() + ".json"), 8192)
    if (_canonical(manifest) != _canonical(expected) or _read(directory / "session.sha256", 128).decode("ascii").strip() != checksum
            or _strict_json(claim_raw) != {"schema_version": 1, "identity": identity, "session_dir": str(directory)}
            or len(events) != 1 or events[0]["event"] != "structured_session_prepared"
            or events[0]["data"] != {"session_sha256": checksum, "access_sha256": sha256(claim_raw).hexdigest(),
                                     "budget": BUDGET, "source_model_requests": 1, "new_model_requests": 0, "new_api_cost_usd": "0"}):
        raise ValueError("La sesión, su ubicación, reserva, código o fuentes han cambiado.")
    return manifest, proposal


def structured_session_usage(session_dir: str | Path) -> dict:
    session = Path(session_dir).resolve()
    _, proposal = _load(session)
    def count(key):
        values = [item.get(key) if isinstance(item, dict) else None for item in proposal["usage"]]
        return sum(values) if all(type(value) is int and value >= 0 for value in values) else None
    path = session / "budget/backtests.json"
    if path.exists() and _strict_json(_read(path, 4096))["reserved_backtests"] != 2:
        raise ValueError("La reserva global de simulaciones ha cambiado.")
    return {"source_model_requests": proposal["model_requests"], "new_model_requests": 0,
            "source_input_tokens": count("input_tokens"), "source_output_tokens": count("output_tokens"),
            "source_api_cost_usd": proposal["api_cost_usd"], "new_api_cost_usd": "0",
            "reserved_backtests": 2 if path.exists() else 0}


@contextmanager
def _action(session: Path):
    manifest, proposal = _load(session)
    journal = RunJournal(session / "attempts")
    raw = _canonical({"action": "finish", "attempt": str(journal.directory)})
    lock, owned = session / "active.lock", False
    journal.record("structured_finish_started")
    try:
        try:
            _write_exclusive(lock, raw)
        except FileExistsError as error:
            raise ValueError("La sesión está ocupada o conserva un bloqueo tras una interrupción.") from error
        owned = True
        def checkpoint():
            current, _ = _load(session)
            if _canonical(current) != _canonical(manifest) or _read(lock, 4096) != raw:
                raise ValueError("La sesión o su bloqueo han cambiado durante la acción.")
        yield manifest, proposal, journal, checkpoint
    except Exception as error:
        journal.record("structured_finish_failed", error_type=type(error).__name__, message=str(error)[:1000],
                       child_run=str(error.directory) if hasattr(error, "directory") else None)
        raise StructuredSessionError(str(error), journal.directory) from error
    finally:
        if owned and lock.exists() and lock.read_bytes() == raw:
            lock.unlink()


def finish_structured_session(session_dir: str | Path, assessment: dict) -> Path:
    session = Path(session_dir).resolve()
    with _action(session) as (manifest, proposal, journal, checkpoint):
        validate_assessment(assessment, proposal, manifest["source"])
        _claim_action(session, journal, "finish")
        frozen = Path(manifest["reference"]["frozen_dir"])
        artifacts = {}
        def registered(kind, directory, files):
            checkpoint()
            artifacts[kind] = _origin(directory, files)
            journal.record("artifact_registered", kind=kind, origin=artifacts[kind])
        root = session / "a"
        review = review_structured_idea(manifest["source"]["directory"], frozen, assessment=assessment, output_dir=root / "r")
        registered("review", review, ("review.json", "review.json.sha256", "events.jsonl"))
        reviewed = verify_structured_review(review, frozen)
        state, conclusion = reviewed["status"], None
        if state == "accepted":
            plan = prepare_structured_plan(review, frozen, output_dir=root / "p")
            registered("plan", plan, ("plan.json", "plan.json.sha256", "events.jsonl", "development.xml"))
            (session / "budget").mkdir(exist_ok=True)
            _write_exclusive(session / "budget/backtests.json", _canonical({"reserved_backtests": 2, "attempt": str(journal.directory)}))
            journal.record("session_backtests_reserved", reserved_backtests=2)
            execution = execute_structured_plan(plan, frozen, output_dir=root / "x")
            registered("execution", execution, ("results.json", "report.md", "baseline.json", "candidate.json", "development.xml", "events.jsonl"))
            conclusion = verify_structured_execution(execution, frozen)["assessment"]
            state = "completed"
        checkpoint()
        value = {"schema_version": 1, "state": state, "artifacts": artifacts, "usage": structured_session_usage(session),
                 "assessment": conclusion, "scope": "known_development_history_only", "automatic_followup_experiments": 0}
        _save_stage(journal, "outcome.json", value, "structured_finish_completed")
        return journal.directory


def structured_session_status(session_dir: str | Path) -> dict:
    session = Path(session_dir).resolve()
    manifest, _ = _load(session)
    state, assessment = "awaiting_review", None
    if (session / "actions/finish.json").exists():
        try:
            value = _stage(session, "finish", "outcome.json", "structured_finish_completed")
            review = _inside(session, value["artifacts"]["review"]["directory"])
            reviewed = verify_structured_review(review, Path(manifest["reference"]["frozen_dir"]))
            if reviewed["source"] != manifest["source"]:
                raise ValueError("La revisión no pertenece a la propuesta de esta sesión.")
            state, assessment = reviewed["status"], None
            if state == "accepted":
                execution = _inside(session, value["artifacts"]["execution"]["directory"])
                result = verify_structured_execution(execution, Path(manifest["reference"]["frozen_dir"]))
                if set(value["artifacts"]) != {"review", "plan", "execution"} or result["plan"] != value["artifacts"]["plan"]:
                    raise ValueError("El resultado no corresponde al plan registrado por esta sesión.")
                plan = _strict_json(_read(Path(result["plan"]["directory"]) / "plan.json", 131072))
                if (plan["review"]["directory"] != str(review) or any(
                        value["artifacts"]["review"]["sha256"].get(name) != checksum
                        for name, checksum in plan["review"]["sha256"].items())):
                    raise ValueError("El plan no procede de la revisión de esta sesión.")
                assessment = result["assessment"]
                state = "completed"
            elif set(value["artifacts"]) != {"review"}:
                raise ValueError("Una revisión no aceptada no puede contener cálculos.")
            if (value["state"] != state or value["assessment"] != assessment or value["automatic_followup_experiments"] != 0
                    or value["usage"] != structured_session_usage(session) or value["scope"] != manifest["scope"]):
                raise ValueError("El cierre no coincide con la revisión o los resultados del motor.")
        except (ValueError, KeyError, TypeError, IndexError, OSError, RecursionError):
            state, assessment = "finish_incomplete_or_invalid", None
    return {"session": str(session), "state": state, "assessment": assessment,
            "active_or_interrupted": (session / "active.lock").exists(), "budget": manifest["budget"],
            "usage": structured_session_usage(session), "scope": manifest["scope"]}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — sesión de revisión y ejecución desde propuesta estructurada")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("--proposal-run", type=Path, required=True)
    create.add_argument("--frozen-run", type=Path, required=True)
    create.add_argument("--output-dir", type=Path, default=ROOT / ".local/structured-sessions")
    for name in ("finish", "status"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--session", type=Path, required=True)
        if name == "finish":
            cmd.add_argument("--assessment", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            directory = create_structured_session(args.proposal_run, args.frozen_run, output_dir=args.output_dir)
        elif args.command == "finish":
            directory = finish_structured_session(args.session, _strict_json(_read(args.assessment, 16384)))
        else:
            print(json.dumps(structured_session_status(args.session), ensure_ascii=False))
            return
    except StructuredSessionError as error:
        parser.exit(1, f"Sesión detenida: {error}. Evidencia: {error.directory}\n")
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"Sesión no verificable: {error}\n")
    print(f"Registro: {directory}")


if __name__ == "__main__":
    main()
