"""Ciclo acotado de investigación: propuesta, revisión técnica y ejecución separadas."""

import argparse
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path

from trading_ai.agent_feedback import (_code_hashes as _feedback_hashes, analyze_execution,
                                       revise_idea, verify_revision)
from trading_ai.ai import AIConfig, ResearchProvider, create_provider, load_ai_config
from trading_ai.discovery import DEFAULT_QUESTION
from trading_ai.formalization import _read, _strict_json, formalize_idea
from trading_ai.holdout import _write_exclusive
from trading_ai.idea_memory import capture_memory, discover_with_memory, duplicate_of, fingerprint, validate_memory
from trading_ai.research import ROOT, RunJournal, _api_cost
from trading_ai.robustness import _development
from trading_ai.rule_execution import execute_rule_plan, verify_rule_execution
from trading_ai.rule_planning import (_canonical, _translation, prepare_rule_plan, review_translation,
                                      validate_assessment as validate_review_assessment, verify_review)


BUDGET = {"initial_ideas": 1, "revisions": 1, "model_requests": 5, "backtests": 2,
          "max_output_tokens_per_request": 384, "automatic_retries": 0}


class SessionError(ValueError):
    def __init__(self, message: str, directory: Path):
        super().__init__(message)
        self.directory = directory


def _code_hashes() -> dict:
    return {**_feedback_hashes(), **{name: sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                                  for name in ("research_session.py", "idea_memory.py")}}


def _config(config: AIConfig) -> None:
    if config.provider != "ollama":
        raise ValueError("La sesión solo admite Ollama local; OpenAI sigue reservado.")
    if config.output_tokens > 384 or config.context_tokens > 4096:
        raise ValueError("La sesión admite hasta 384 tokens de salida y 4096 de contexto por petición.")


def _manifest(directory: Path, reference: dict, config: AIConfig, question: str, memory_sha256: str) -> dict:
    _config(config)
    if not isinstance(question, str) or not question.strip() or len(question) > 800:
        raise ValueError("La pregunta debe contener entre 1 y 800 caracteres.")
    return {"schema_version": 2, "protocol": "bounded_research_session_v2", "session_dir": str(directory),
            "reference": reference, "ai_config": asdict(config), "question": question,
            "memory_sha256": memory_sha256,
            "budget": deepcopy(BUDGET), "scope": "known_development_history_only",
            "technical_review_required": True, "outer_evaluation_allowed": False, "code_sha256": _code_hashes()}


def create_session(frozen_dir: str | Path, *, config: AIConfig = AIConfig(), question: str = DEFAULT_QUESTION,
                   output_dir: str | Path = ROOT / ".local/research-sessions") -> Path:
    _config(config)
    if not isinstance(question, str) or not question.strip() or len(question) > 800:
        raise ValueError("La pregunta debe contener entre 1 y 800 caracteres.")
    _, reference, _ = _development(Path(frozen_dir).resolve())
    memory = capture_memory(Path(frozen_dir).resolve())
    validate_memory(memory, reference)
    journal = RunJournal(Path(output_dir).resolve())
    journal.save("memory.json", memory)
    manifest = _manifest(journal.directory, reference, config, question,
                         sha256((journal.directory / "memory.json").read_bytes()).hexdigest())
    journal.save("session.json", manifest)
    checksum = sha256((journal.directory / "session.json").read_bytes()).hexdigest()
    _write_exclusive(journal.directory / "session.sha256", (checksum + "\n").encode("ascii"))
    journal.record("session_prepared", session_sha256=checksum, budget=manifest["budget"], model_requests=0, api_cost_usd="0")
    return journal.directory


def _load(directory: Path) -> dict:
    raw = _read(directory / "session.json", 65536)
    manifest = _strict_json(raw)
    if manifest.get("protocol") != "bounded_research_session_v2":
        raise ValueError("Sesión de un protocolo anterior: conservar su historial y crear una sesión nueva con memoria.")
    checksum = sha256(raw).hexdigest()
    events = [_strict_json(line) for line in _read(directory / "events.jsonl", 65536).splitlines()]
    _, reference, _ = _development(Path(manifest["reference"]["frozen_dir"]))
    memory_raw = _read(directory / "memory.json", 2 * 1024 * 1024)
    validate_memory(_strict_json(memory_raw), reference)
    expected = _manifest(directory, reference, AIConfig(**manifest["ai_config"]), manifest["question"],
                         sha256(memory_raw).hexdigest())
    if (_read(directory / "session.sha256", 128).decode("ascii").strip() != checksum
            or not events or events[-1]["event"] != "session_prepared"
            or events[-1]["data"]["session_sha256"] != checksum or _canonical(manifest) != _canonical(expected)):
        raise ValueError("La sesión, su ubicación, los datos o el código han cambiado.")
    return manifest


def _inside(directory: Path, path: str | Path) -> Path:
    result = Path(path).resolve()
    if not result.is_relative_to(directory):
        raise ValueError("El archivo de la sesión está fuera de su carpeta registrada.")
    return result


def _origin(directory: Path, files: tuple[str, ...]) -> dict:
    return {"directory": str(directory), "sha256": {
        name: sha256(_read(directory / name, 32 * 1024 * 1024)).hexdigest() for name in files}}


def _check_origin(session: Path, origin: dict) -> Path:
    directory = _inside(session, origin["directory"])
    for name, checksum in origin["sha256"].items():
        if Path(name).name != name or sha256(_read(directory / name, 32 * 1024 * 1024)).hexdigest() != checksum:
            raise ValueError("Un archivo del ciclo ha cambiado.")
    return directory


def session_usage(session_dir: str | Path) -> dict:
    directory = Path(session_dir).resolve()
    manifest = _load(directory)
    slots = []
    for number in range(1, BUDGET["model_requests"] + 1):
        path = directory / "budget" / f"model-{number}.json"
        if path.exists():
            record = _strict_json(_read(path, 4096))
            if record["ordinal"] != number or record["max_output_tokens"] != manifest["ai_config"]["output_tokens"]:
                raise ValueError("La reserva de consultas ha cambiado.")
            slots.append(record)
    usage_by_slot = {}
    for attempt in {item["attempt"] for item in slots}:
        attempt_dir = _inside(directory, attempt)
        for line in _read(attempt_dir / "events.jsonl", 4 * 1024 * 1024).splitlines():
            event = _strict_json(line)
            if event["event"] == "session_model_usage":
                number = event["data"]["ordinal"]
                if number in usage_by_slot:
                    raise ValueError("Consumo duplicado para una reserva de modelo.")
                usage_by_slot[number] = event["data"]["usage"]
    usages = [usage_by_slot.get(item["ordinal"]) for item in slots]
    def tokens(key):
        values = [usage.get(key) if isinstance(usage, dict) else None for usage in usages]
        return sum(values) if all(type(value) is int and value >= 0 for value in values) else None
    backtests = directory / "budget/backtests.json"
    if backtests.exists() and _strict_json(_read(backtests, 4096))["reserved_backtests"] != 2:
        raise ValueError("La reserva de simulaciones ha cambiado.")
    return {"reserved_model_requests": len(slots), "reserved_output_tokens": len(slots) * manifest["ai_config"]["output_tokens"],
            "input_tokens": tokens("input_tokens"), "output_tokens": tokens("output_tokens"),
            "api_cost_usd": "0" if not slots else (_api_cost(usages) if all(isinstance(item, dict) for item in usages) else None),
            "reserved_backtests": 2 if backtests.exists() else 0}


@contextmanager
def _action(directory: Path, name: str):
    manifest = _load(directory)
    journal = RunJournal(directory / "attempts")
    raw = _canonical({"action": name, "attempt": str(journal.directory)})
    lock = directory / "active.lock"
    owned = False
    journal.record("action_started", action=name)
    try:
        try:
            _write_exclusive(lock, raw)
        except FileExistsError as error:
            raise ValueError("La sesión está ocupada o conserva un bloqueo tras una interrupción.") from error
        owned = True
        def checkpoint():
            if _canonical(_load(directory)) != _canonical(manifest) or lock.read_bytes() != raw:
                raise ValueError("La sesión o su bloqueo han cambiado durante la acción.")
        yield manifest, journal, checkpoint
    except Exception as error:
        journal.record("action_failed", action=name, error_type=type(error).__name__, message=str(error)[:1000],
                       child_run=str(error.directory) if hasattr(error, "directory") else None)
        raise SessionError(str(error), journal.directory) from error
    finally:
        if owned and lock.exists() and lock.read_bytes() == raw:
            lock.unlink()


def _claim_action(session: Path, journal: RunJournal, action: str):
    (session / "actions").mkdir(exist_ok=True)
    try:
        _write_exclusive(session / "actions" / (action + ".json"), _canonical({"attempt": str(journal.directory)}))
    except FileExistsError as error:
        raise ValueError("La acción ya tiene un intento registrado; no se repetirá.") from error


class _BudgetProvider:
    def __init__(self, provider: ResearchProvider, session: Path, journal: RunJournal, checkpoint):
        self.provider, self.session, self.journal, self.checkpoint = provider, session, journal, checkpoint

    def describe(self):
        self.checkpoint()
        return self.provider.describe()

    def complete(self, messages, schema):
        self.checkpoint()
        manifest = _load(self.session)
        (self.session / "budget").mkdir(exist_ok=True)
        for number in range(1, BUDGET["model_requests"] + 1):
            record = {"ordinal": number, "attempt": str(self.journal.directory),
                      "max_output_tokens": manifest["ai_config"]["output_tokens"]}
            try:
                _write_exclusive(self.session / "budget" / f"model-{number}.json", _canonical(record))
                break
            except FileExistsError:
                continue
        else:
            raise ValueError("Presupuesto global de consultas agotado.")
        self.journal.record("session_model_reserved", **record)
        try:
            reply = self.provider.complete(messages, schema)
        except Exception as error:
            self.journal.record("session_model_usage", ordinal=number, usage=getattr(error, "usage", None))
            raise
        self.journal.record("session_model_usage", ordinal=number, usage=reply.usage)
        return reply


def _save_stage(journal: RunJournal, filename: str, value: dict, event: str):
    journal.save(filename, value)
    journal.record(event, sha256=sha256((journal.directory / filename).read_bytes()).hexdigest(), state=value["state"])


def _stage(session: Path, action: str, filename: str, event: str) -> dict:
    claim = _strict_json(_read(session / "actions" / (action + ".json"), 4096))
    attempt = _inside(session, claim["attempt"])
    raw = _read(attempt / filename, 131072)
    events = [_strict_json(line) for line in _read(attempt / "events.jsonl", 4 * 1024 * 1024).splitlines()]
    if not events or events[-1]["event"] != event or events[-1]["data"]["sha256"] != sha256(raw).hexdigest():
        raise ValueError("La etapa no tiene un cierre completo verificable.")
    value = _strict_json(raw)
    for origin in value["artifacts"].values():
        _check_origin(session, origin)
    return value


def propose_session(session_dir: str | Path, *, provider: ResearchProvider | None = None) -> Path:
    session = Path(session_dir).resolve()
    with _action(session, "propose") as (manifest, journal, checkpoint):
        _claim_action(session, journal, "propose")
        frozen = Path(manifest["reference"]["frozen_dir"])
        wrapped = _BudgetProvider(provider or create_provider(AIConfig(**manifest["ai_config"])), session, journal, checkpoint)
        artifacts = {}
        def registered(kind, directory, files):
            checkpoint()
            origin = _origin(directory, files)
            artifacts[kind] = origin
            journal.record("artifact_registered", kind=kind, origin=origin)
        # Rutas compactas: anidar UUID de sesión, acción y herramienta supera MAX_PATH en Windows.
        artifacts_dir = session / "a"
        memory = _strict_json(_read(session / "memory.json", 2 * 1024 * 1024))
        idea = discover_with_memory(wrapped, frozen, memory, question=manifest["question"], output_dir=artifacts_dir / "i")
        registered("root_idea", idea, ("idea.json", "events.jsonl"))
        root = _strict_json(_read(idea / "idea.json", 32768))
        def stop_if_duplicate(directory, *, include_root=False):
            record = _strict_json(_read(directory / "idea.json", 32768))
            matches = duplicate_of(record["proposal"], memory)
            if include_root and fingerprint(record["proposal"]) == fingerprint(root["proposal"]):
                matches.append(root["idea_id"])
            if not matches:
                return False
            journal.record("duplicate_idea_detected", idea_id=record["idea_id"], matches=sorted(set(matches)),
                           validation_scope="cosmetic_rule_fingerprint_not_semantic_equivalence")
            value = {"schema_version": 1, "state": "duplicate_idea", "latest_idea": str(directory),
                     "latest_translation": None, "duplicate_of": sorted(set(matches)), "artifacts": artifacts,
                     "usage": session_usage(session), "executable": False}
            checkpoint()
            _save_stage(journal, "proposal.json", value, "proposal_completed")
            return True
        if stop_if_duplicate(idea):
            return journal.directory
        translation = formalize_idea(wrapped, idea, frozen, output_dir=artifacts_dir / "t")
        registered("root_translation", translation, ("translation.json", "events.jsonl"))
        record = _strict_json((translation / "translation.json").read_bytes())
        if record["status"] == "needs_clarification":
            idea = revise_idea(wrapped, translation, frozen, output_dir=artifacts_dir / "v")
            verify_revision(idea, frozen)
            registered("revised_idea", idea, ("idea.json", "events.jsonl"))
            if stop_if_duplicate(idea, include_root=True):
                return journal.directory
            translation = formalize_idea(wrapped, idea, frozen, output_dir=artifacts_dir / "u")
            registered("revised_translation", translation, ("translation.json", "events.jsonl"))
            record = _strict_json((translation / "translation.json").read_bytes())
        state = "awaiting_review" if record["status"] == "pending_semantic_review" else record["status"]
        value = {"schema_version": 1, "state": state, "latest_idea": str(idea), "latest_translation": str(translation),
                 "artifacts": artifacts, "usage": session_usage(session), "executable": False}
        checkpoint()
        _save_stage(journal, "proposal.json", value, "proposal_completed")
        return journal.directory


def finish_session(session_dir: str | Path, assessment: dict, *, provider: ResearchProvider | None = None) -> Path:
    session = Path(session_dir).resolve()
    with _action(session, "finish") as (manifest, journal, checkpoint):
        proposal = _stage(session, "propose", "proposal.json", "proposal_completed")
        if proposal["state"] != "awaiting_review":
            raise ValueError("La propuesta no tiene reglas listas para revisión técnica.")
        translation, translation_origin = _translation(_inside(session, proposal["latest_translation"]),
                                                      Path(manifest["reference"]["frozen_dir"]))
        validate_review_assessment(assessment, translation, translation_origin)
        _claim_action(session, journal, "finish")
        frozen = Path(manifest["reference"]["frozen_dir"])
        artifacts = {}
        def registered(kind, directory, files):
            checkpoint()
            origin = _origin(directory, files)
            artifacts[kind] = origin
            journal.record("artifact_registered", kind=kind, origin=origin)
        if "revised_idea" in proposal["artifacts"]:
            verify_revision(Path(proposal["latest_idea"]), frozen)
        artifacts_dir = session / "a"
        review = review_translation(_inside(session, proposal["latest_translation"]), frozen, assessment=assessment,
                                    output_dir=artifacts_dir / "r")
        registered("review", review, ("review.json", "review.json.sha256", "events.jsonl"))
        reviewed = verify_review(review, frozen)
        state = reviewed["status"]
        if state == "accepted":
            plan = prepare_rule_plan(review, frozen, output_dir=artifacts_dir / "p")
            registered("plan", plan, ("plan.json", "plan.json.sha256", "development.xml", "events.jsonl"))
            (session / "budget").mkdir(exist_ok=True)
            _write_exclusive(session / "budget/backtests.json", _canonical({"reserved_backtests": 2, "attempt": str(journal.directory)}))
            journal.record("session_backtests_reserved", reserved_backtests=2)
            execution = execute_rule_plan(plan, frozen, output_dir=artifacts_dir / "x")
            registered("execution", execution, ("results.json", "report.md", "baseline.json", "candidate.json", "development.xml", "events.jsonl"))
            verify_rule_execution(execution, frozen)
            wrapped = _BudgetProvider(provider or create_provider(AIConfig(**manifest["ai_config"])), session, journal, checkpoint)
            analysis = analyze_execution(wrapped, execution, frozen, output_dir=artifacts_dir / "n")
            registered("analysis", analysis, ("analysis.json", "events.jsonl"))
            state = "completed"
        checkpoint()
        _stage(session, "propose", "proposal.json", "proposal_completed")
        value = {"schema_version": 1, "state": state, "artifacts": artifacts, "usage": session_usage(session),
                 "scope": "known_development_history_only", "automatic_followup_experiments": 0}
        _save_stage(journal, "outcome.json", value, "finish_completed")
        return journal.directory


def session_status(session_dir: str | Path) -> dict:
    session = Path(session_dir).resolve()
    manifest = _load(session)
    state = "prepared"
    for action, filename, event in (("propose", "proposal.json", "proposal_completed"), ("finish", "outcome.json", "finish_completed")):
        if (session / "actions" / (action + ".json")).exists():
            try:
                state = _stage(session, action, filename, event)["state"]
            except (ValueError, KeyError, TypeError, OSError):
                state = action + "_incomplete_or_invalid"
                break
    return {"session": str(session), "state": state, "active_or_interrupted": (session / "active.lock").exists(),
            "budget": manifest["budget"], "usage": session_usage(session), "scope": manifest["scope"]}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Trading AI — sesión de investigación con presupuesto global")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("--frozen-run", type=Path, required=True)
    create.add_argument("--config", type=Path)
    create.add_argument("--question", default=DEFAULT_QUESTION)
    create.add_argument("--output-dir", type=Path, default=ROOT / ".local/research-sessions")
    for name in ("propose", "finish", "status"):
        command = commands.add_parser(name)
        command.add_argument("--session", type=Path, required=True)
        if name == "finish":
            command.add_argument("--assessment", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "create":
            result = create_session(args.frozen_run, config=load_ai_config(args.config), question=args.question, output_dir=args.output_dir)
        elif args.command == "propose":
            result = propose_session(args.session)
        elif args.command == "finish":
            result = finish_session(args.session, _strict_json(_read(args.assessment, 16384)))
        else:
            print(json.dumps(session_status(args.session), ensure_ascii=False))
            return
    except SessionError as error:
        parser.exit(1, f"Sesión detenida: {error}. Registro: {error.directory}\n")
    except (ValueError, TypeError, KeyError, IndexError, OSError, RecursionError) as error:
        parser.exit(1, f"No se pudo preparar o verificar la sesión: {error}\n")
    print(f"Registro de sesión: {result}")


if __name__ == "__main__":
    main()
