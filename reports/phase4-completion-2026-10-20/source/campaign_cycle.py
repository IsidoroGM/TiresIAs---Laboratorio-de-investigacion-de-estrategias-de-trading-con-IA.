"""Ciclo local acotado: transporte, revisión mecánica, motor y memoria separados.

Contrato nuevo de laboratorio. No convierte revisiones pendientes en aceptadas,
no acredita comprensión semántica de prosa y no adopta estrategias.
"""

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from trading_ai import PROJECT_NAME
from trading_ai import campaign_attempts as attempts
from trading_ai import campaign_context as context
from trading_ai import campaign_ledger as ledger
from trading_ai import rule_execution as engine
from trading_ai.ai import AIConfig, OllamaProvider, ProviderError, ProviderReply
from trading_ai.compact_ollama import CompactOllamaProvider
from trading_ai.data import load_ecb_rates
from trading_ai.formalization import _read, _strict_json
from trading_ai.holdout import _policy, _write_exclusive
from trading_ai.research import ROOT, RunJournal
from trading_ai.research_session import _origin
from trading_ai.rule_planning import _artifact, _canonical, _seal
from trading_ai.rules import compile_rule_strategy
from trading_ai.strategies import create_strategy
from trading_ai.structured_draft import describe_draft, DRAFT_SCHEMA
from trading_ai.verification_session import VerificationSession


ACCESS_ROOT = ROOT / ".local/campaign-cycle-access"
PERMIT_FILES = ("permit.json", "permit.json.sha256", "development.xml", "events.jsonl")
EXECUTION_POLICY = {"accounts": "independent_per_partition_and_pair", "carry_positions": False,
                    "carry_signals": False, "indicator_warmup": "inside_each_partition"}
ERRORS = (ValueError, OSError, KeyError, TypeError, IndexError, RecursionError)


class CampaignProvider(CompactOllamaProvider):
    """Mismo esquema/servidor/contexto; esquema fijo por huella en la captura.

    El esquema se transmite íntegro como format, no se repite dentro del contexto.
    Registro <=12 KiB y envoltura de mensajes+esquema <=24 KiB; los 4096 tokens
    siguen siendo el límite del modelo y un exceso se rechaza sin recortes.
    """
    def complete(self, messages, schema):
        self._model_attempted, self.last_response = False, None
        used, start = None, self.metadata_requests
        try:
            packet = {"messages": messages, "schema_sha256": sha256(_canonical(schema)).hexdigest()}
            if (_canonical(schema) != _canonical(DRAFT_SCHEMA) or len(_canonical(packet)) > 12288
                    or len(_canonical({"messages": messages, "schema": schema})) > 24576
                    or not isinstance(messages, list) or len(messages) != 2
                    or [item.get("role") for item in messages if isinstance(item, dict)] != ["system", "user"]
                    or any(set(item) != {"role", "content"} or not isinstance(item["content"], str) or not item["content"].strip() for item in messages)):
                raise ProviderError("Petición de campaña o esquema fijo no admitidos.")
            reply = OllamaProvider.complete(self, messages, schema)
            used = dict(reply.usage)
            inputs, outputs = used.get("input_tokens"), used.get("output_tokens")
            if (type(inputs) is not int or inputs < 1 or type(outputs) is not int or outputs < 1
                    or outputs > self.config.output_tokens or inputs + outputs > self.config.context_tokens):
                raise ProviderError("Consumo de contexto desconocido o excedido.", used)
            self.describe()
            return ProviderReply(reply.content, reply.model, {**used, "metadata_request_attempts": self.metadata_requests - start})
        except ProviderError as error:
            usage = error.usage if error.usage is not None else used
            if usage is None:
                value = None if self._model_attempted else 0
                usage = {"input_tokens": value, "output_tokens": value, "api_cost_usd": "0"}
            raise ProviderError(str(error), {**usage, "metadata_request_attempts": self.metadata_requests - start}) from error


def _code_hashes():
    return {**attempts._code_hashes(), **engine._code_hashes(),
            **{name: sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
               for name in ("campaign_context.py", "campaign_cycle.py", "compact_ollama.py", "verification_session.py")}}


def _contract(scope_id, directory, state, plan, legacy, content):
    record = {"schema_version": 1, "protocol": "controlled_local_campaign_permit_v1", "run_dir": str(directory),
              "scope_id": scope_id, "registration": state["registration"], "reference": plan["reference"],
              "policy": plan["controls"], "criterion": plan["objective"]["criterion"], "data": plan["data"],
              "limits": plan["limits"], "legacy": legacy, "legacy_sha256": sha256(_canonical(legacy)).hexdigest(),
              "initial_consumed_rule_identities": plan["history"]["consumed_rule_identities"],
              "source_sha256": sha256(content).hexdigest(), "execution_policy": EXECUTION_POLICY,
              "review_policy": "mechanical_closed_typed_rules_for_virtual_experiment_only",
              "request_policy": {"capture_bytes": 12288, "messages_and_schema_bytes": 24576, "context_tokens": 4096,
                                 "output_tokens": 384, "truncate": False, "shift": False, "schema_in_capture": "sha256_of_fixed_DRAFT_SCHEMA"},
              "semantic_acceptance": False, "automatic_adoption": False, "outer_evaluation_allowed": False,
              "broker_operations_allowed": False, "api_cost_usd": "0", "automatic_retries": 0,
              "inherited_usage": state["registration"]["inherited_usage"], "code_sha256": _code_hashes()}
    return record, content


def _permit(scope_id, directory):
    state, plan, legacy, content = context.sources(scope_id)
    if state["reservations"]: raise ValueError("Este contrato comienza sin reservas de campaña; no migra o reinicia intentos anteriores.")
    if plan["limits"]["max_backtests"] < 2: raise ValueError("El ciclo requiere al menos una comparación virtual permitida.")
    return _contract(scope_id, directory, state, plan, legacy, content)


def prepare_cycle(scope_id, *, output_dir=ROOT / ".local/campaign-cycle-permits"):
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("cycle_permit_started", scope_id=scope_id)
    try:
        record, content = _permit(scope_id, journal.directory)
        if (ACCESS_ROOT / (scope_id + ".json")).exists(): raise ValueError("El ciclo de este ámbito ya tiene un intento; no se reabre.")
        # Comprueba encaje por bytes antes de conceder un intento o consultar modelos.
        context.build_request(scope_id, record["legacy"], [], record["initial_consumed_rule_identities"])
        _write_exclusive(journal.directory / "development.xml", content)
        if _canonical(_permit(scope_id, journal.directory)[0]) != _canonical(record): raise ValueError("Las fuentes cambiaron durante la preparación.")
        _seal(journal, "permit.json", record, "cycle_permit_prepared")
    except Exception as error:
        journal.record("cycle_permit_failed", error_type=type(error).__name__, message=str(error)[:1000], model_requests=0, backtests=0, api_cost_usd="0")
        raise
    return journal.directory


def verify_permit(directory):
    directory = Path(directory).resolve()
    record, _ = _artifact(directory, "permit.json", "cycle_permit_prepared")
    state, plan, legacy, content = context.sources(record["scope_id"])
    if (record["run_dir"] != str(directory) or record["registration"] != state["registration"]
            or record["policy"] != plan["controls"] or record["limits"] != plan["limits"]
            or record["reference"] != plan["reference"] or record["legacy"] != legacy
            or record["source_sha256"] != sha256(content).hexdigest()
            or _read(directory / "development.xml", 32 * 1024 * 1024) != content
            or record["code_sha256"] != _code_hashes()):
        raise ValueError("El permiso, datos, historial o código cambiaron.")
    expected, _ = _contract(record["scope_id"], directory, state, plan, legacy, content)
    if _canonical(record) != _canonical(expected): raise ValueError("El contrato del ciclo ha cambiado.")
    return record


def review_rules(draft, consumed, observations):
    described = describe_draft(draft)
    if described["spec_sha256"] in consumed: return {"status": "duplicate_rules", "eligible_for_experiment": False, **described}
    windows = []
    for rule in (draft["entry"], draft["exit"]):
        for operand in (rule["left"], rule["right"]):
            if operand["kind"] != "constant": windows.append(operand.get("window", 1) + operand["lag"])
    sufficient = not windows or max(windows) < observations
    return {**described, "status": "mechanically_reviewed" if sufficient else "insufficient_data",
            "eligible_for_experiment": sufficient, "review_origin": "python_closed_typed_contract",
            "semantic_acceptance": False, "automatic_adoption": False}


def _assert_state(scope_id, expected):
    if ledger.inspect_campaign(scope_id) != expected: raise ValueError("El registro cambió fuera del ciclo; no se continúa.")


def _advance(previous, reserved):
    if (reserved["reused"] or reserved["state"]["registration"] != previous["registration"]
            or sorted(_canonical(item) for item in reserved["state"]["reservations"])
            != sorted(_canonical(item) for item in previous["reservations"] + [reserved["receipt"]])):
        raise ValueError("Hay reservas ajenas o un intento consumido; no se continúa.")
    return reserved["state"]


def _view(permit, reviewed):
    return {"candidate": {"spec": reviewed["spec"]},
            "baseline": {"strategy": permit["policy"]["baseline_strategy"], "fast_window": permit["policy"]["fast_window"],
                         "slow_window": permit["policy"]["slow_window"]}, "policy": permit["policy"],
            "data": {**permit["data"], "sha256": permit["source_sha256"]},
            "execution_policy": permit["execution_policy"], "execution_timing": "next_observation", "direction": "long_only"}


def run_cycle(permit_dir, *, allow_local_generation=False, allow_virtual_calculations=False,
              output_dir=ROOT / ".local/campaign-cycles"):
    if allow_local_generation is not True or allow_virtual_calculations is not True:
        raise ValueError("Se requieren las dos habilitaciones explícitas: generación local y cálculos virtuales.")
    permit_dir = Path(permit_dir).resolve()
    journal = RunJournal(Path(output_dir).resolve())
    journal.record("cycle_started", permit_dir=str(permit_dir))
    entries, consumed, stop = [], set(), "budget_exhausted"
    try:
        permit = verify_permit(permit_dir)
        state = ledger.inspect_campaign(permit["scope_id"])
        if state["reservations"]: raise ValueError("Ya existen intentos; este ciclo no los reanuda.")
        origin = _origin(permit_dir, PERMIT_FILES)
        access = ACCESS_ROOT / (permit["scope_id"] + ".json")
        ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
        claim = {"schema_version": 1, "protocol": "local_campaign_cycle_claim_v1", "scope_id": permit["scope_id"],
                 "run_dir": str(journal.directory), "permit": origin, "code_sha256": _code_hashes()}
        _write_exclusive(access, _canonical(claim))
        consumed.update(permit["initial_consumed_rule_identities"])
        provider = CampaignProvider(AIConfig())
        identity = provider.describe()
        journal.save("provider.json", identity)
        pinned_files = {"provider.json": sha256((journal.directory / "provider.json").read_bytes()).hexdigest()}
        policy = _policy(permit["policy"])
        data_path = permit_dir / "development.xml"
        rates = tuple(load_ecb_rates(data_path, policy.pair))
        if len(rates) != permit["data"]["observations"]: raise ValueError("Observaciones distintas de las registradas.")

        def unchanged():
            if (verify_permit(permit_dir) != permit or _origin(permit_dir, PERMIT_FILES) != origin
                    or _read(access, 262144) != _canonical(claim)):
                raise ValueError("Fuentes o permiso del ciclo cambiaron.")
            _assert_state(permit["scope_id"], state)
            for name, digest in pinned_files.items():
                if sha256(_read(journal.directory / name, 32 * 1024 * 1024)).hexdigest() != digest:
                    raise ValueError("Cambió un resultado, revisión o plan anterior.")
            for previous in entries:
                if "capture_source" in previous:
                    directory = Path(previous["capture_source"]["directory"])
                    if _origin(directory, tuple(previous["capture_source"]["sha256"])) != previous["capture_source"]:
                        raise ValueError("Una captura anterior cambió durante el ciclo.")

        for number in range(permit["limits"]["max_proposals"]):
            unchanged()
            if state["remaining_accounting_slots"]["proposals"] < 1 or state["remaining_accounting_slots"]["backtests"] < 2: break
            try: raw, request_meta = context.build_request(permit["scope_id"], permit["legacy"], entries, consumed)
            except ValueError as error:
                if not str(error).startswith("context_overflow:"): raise
                stop = "context_overflow_before_request"
                break
            receipt = ledger.reserve_proposal(permit["scope_id"], sha256(raw).hexdigest())
            state = _advance(state, receipt)
            request_sha = receipt["receipt"]["operation_id"]
            capture = attempts.prepare_attempt(permit["scope_id"], raw)
            attempts.mark_submission_intent(permit["scope_id"], request_sha)
            unchanged()
            payload = _strict_json(raw)
            error, reply = None, None
            try: reply = provider.complete(payload["messages"], DRAFT_SCHEMA)
            except ProviderError as failure: error = failure
            usage = dict(reply.usage) if reply else error.usage
            attempted = provider._model_attempted
            observation = {"model_request_attempted": attempted, "content": reply.content if reply else None,
                           "model": reply.model if reply else None,
                           "usage": {key: usage.get(key) for key in ("input_tokens", "output_tokens", "api_cost_usd")} if usage else None,
                           "error": {"type": type(error).__name__, "message": str(error)} if error else None,
                           "provider_response": {"json": deepcopy(provider.last_response), "metadata_requests": provider.metadata_requests}}
            completion = attempts.record_observation(permit["scope_id"], request_sha, _canonical(observation))
            entry = {"number": number + 1, "request": request_meta, "receipt": receipt["receipt"],
                     "capture": str(capture), "capture_source": _origin(capture, tuple(name for name in context.controller.CAPTURE_FILES if (capture / name).is_file())),
                     "content": observation["content"], "usage": completion["analysis"]["usage"],
                     "error": observation["error"], "review": None, "results": None,
                     "transport_origin": "application_controlled_loopback_parsed_json", "provider_identity": identity}
            entries.append(entry)
            journal.save(f"proposal-{number+1:02d}.json", entry)
            pinned_files[f"proposal-{number+1:02d}.json"] = sha256((journal.directory / f"proposal-{number+1:02d}.json").read_bytes()).hexdigest()
            if completion["analysis"]["requires_stop"] or error:
                stop = "provider_error_or_unknown_usage"
                break
            draft = _strict_json(reply.content)
            reviewed = review_rules(draft, consumed, len(rates))
            entry["review"] = reviewed
            journal.save(f"review-{number+1:02d}.json", reviewed)
            pinned_files[f"review-{number+1:02d}.json"] = sha256((journal.directory / f"review-{number+1:02d}.json").read_bytes()).hexdigest()
            if not reviewed["eligible_for_experiment"]:
                stop = reviewed["status"]
                break
            consumed.add(reviewed["spec_sha256"])
            unchanged()
            view = _view(permit, reviewed)
            calculation_id = sha256(_canonical(engine._identity(view))).hexdigest()
            calculation_claim = engine.ACCESS_ROOT / (calculation_id + ".json")
            engine.ACCESS_ROOT.mkdir(parents=True, exist_ok=True)
            calculation_raw = _canonical({"protocol": "local_cycle_calculation_v1", "identity": engine._identity(view),
                                         "run_dir": str(journal.directory), "scope_id": permit["scope_id"],
                                         "request_sha256": request_sha, "code_sha256": _code_hashes()})
            _write_exclusive(calculation_claim, calculation_raw)
            entry["calculation_claim"] = {"path": str(calculation_claim), "sha256": sha256(calculation_raw).hexdigest()}
            comparison = ledger.reserve_comparison(permit["scope_id"], request_sha, calculation_id)
            state = _advance(state, comparison)
            journal.save(f"plan-{number+1:02d}.json", {**view, "calculation_id": calculation_id, "comparison": comparison["receipt"],
                         "criterion": permit["criterion"], "review": reviewed, "context_sha256": request_meta["sha256"]})
            pinned_files[f"plan-{number+1:02d}.json"] = sha256((journal.directory / f"plan-{number+1:02d}.json").read_bytes()).hexdigest()
            calculated = {}
            base = view["baseline"]
            for role, strategy in (("baseline", create_strategy(base["strategy"], base["fast_window"], base["slow_window"])),
                                   ("candidate", compile_rule_strategy(reviewed["spec"]))):
                unchanged()
                if _read(calculation_claim, 262144) != calculation_raw: raise ValueError("La reserva del motor cambió.")
                journal.record("cycle_backtest_attempted", number=number + 1, role=role, calculation_id=calculation_id)
                value = engine._calculate(rates, strategy, policy)
                journal.save(f"{role}-{number+1:02d}.json", value)
                pinned_files[f"{role}-{number+1:02d}.json"] = sha256((journal.directory / f"{role}-{number+1:02d}.json").read_bytes()).hexdigest()
                calculated[role] = value["summary"]
                journal.record("cycle_backtest_completed", number=number + 1, role=role)
            result = {**view, **calculated, "proposal": {"criterion": permit["criterion"]}, "calculation_id": calculation_id}
            result["assessment"] = engine._assessment(result)
            result["artifacts_sha256"] = {name: sha256((journal.directory / name).read_bytes()).hexdigest()
                                         for name in (f"baseline-{number+1:02d}.json", f"candidate-{number+1:02d}.json", f"plan-{number+1:02d}.json")}
            entry["results"] = result
            entry["comparison"] = comparison["receipt"]
            journal.save(f"result-{number+1:02d}.json", result)
            pinned_files[f"result-{number+1:02d}.json"] = sha256((journal.directory / f"result-{number+1:02d}.json").read_bytes()).hexdigest()
            journal.record("cycle_memory_updated", number=number + 1, assessment=result["assessment"])
        unchanged()
        record = {"schema_version": 1, "protocol": "controlled_local_campaign_v1", "run_dir": str(journal.directory),
                  "permit": origin, "scope_id": permit["scope_id"], "stop_reason": stop, "entries": entries,
                  "state": state, "consumed_rule_identities": sorted(consumed), "source_sha256": permit["source_sha256"],
                  "usage": attempts.inspect_attempts(permit["scope_id"]), "api_cost_usd": "0", "automatic_adoption": False,
                  "semantic_acceptance": False, "outer_evaluation_allowed": False, "broker_operations_allowed": False,
                  "scope": "known_development_history_only", "code_sha256": _code_hashes()}
        record["artifacts_sha256"] = pinned_files
        _seal(journal, "cycle.json", record, "cycle_completed")
    except Exception as error:
        journal.record("cycle_failed", error_type=type(error).__name__, message=str(error)[:1000], entries=entries,
                       no_automatic_retry=True, api_cost_usd="0")
        raise engine.ExecutionError(str(error), journal.directory) from error
    return journal.directory


def inspect_cycle(run_dir):
    """Verifica memoria y contabilidad guardadas, sin modelos ni recalcular."""
    directory = Path(run_dir).resolve()
    record, _ = _artifact(directory, "cycle.json", "cycle_completed")
    permit_dir = Path(record["permit"]["directory"])
    permit = verify_permit(permit_dir)
    state = ledger.inspect_campaign(permit["scope_id"])
    if (record["run_dir"] != str(directory) or record["scope_id"] != permit["scope_id"]
            or record["permit"] != _origin(permit_dir, PERMIT_FILES) or record["state"] != state
            or record["code_sha256"] != _code_hashes() or record["source_sha256"] != permit["source_sha256"]
            or record["automatic_adoption"] is not False or record["semantic_acceptance"] is not False
            or record["outer_evaluation_allowed"] is not False or record["broker_operations_allowed"] is not False):
        raise ValueError("La memoria del ciclo, registro o fuentes han cambiado.")
    access = ACCESS_ROOT / (permit["scope_id"] + ".json")
    expected_claim = {"schema_version": 1, "protocol": "local_campaign_cycle_claim_v1", "scope_id": permit["scope_id"],
                      "run_dir": str(directory), "permit": record["permit"], "code_sha256": _code_hashes()}
    if _read(access, 262144) != _canonical(expected_claim): raise ValueError("La memoria no posee el intento del ciclo.")
    for name, digest in record["artifacts_sha256"].items():
        if Path(name).name != name or sha256(_read(directory / name, 32 * 1024 * 1024)).hexdigest() != digest:
            raise ValueError("Un archivo del ciclo cambió.")
    if (len(record["entries"]) > permit["limits"]["max_proposals"]
            or state["reserved_backtests"] > permit["limits"]["max_backtests"]): raise ValueError("Presupuesto del ciclo excedido.")
    consumed, earlier, receipt_ids = set(permit["initial_consumed_rule_identities"]), [], set()
    for number, entry in enumerate(record["entries"], 1):
        raw, metadata = context.build_request(permit["scope_id"], permit["legacy"], earlier, consumed)
        if entry["number"] != number or entry["request"] != metadata or sha256(raw).hexdigest() != entry["receipt"]["operation_id"]:
            raise ValueError("Una petición no contiene la memoria íntegra anterior.")
        receipt_ids.add(entry["receipt"]["receipt_id"])
        capture, _, _, completion = attempts._load(state, entry["receipt"])
        observation = _strict_json(_read(capture / "observation.raw", attempts.MAX_OBSERVATION_BYTES))
        if (entry["capture_source"] != _origin(capture, tuple(entry["capture_source"]["sha256"]))
                or _read(capture / "request.json", 12288) != raw or entry["content"] != observation["content"]
                or entry["usage"] != completion["analysis"]["usage"] or entry["error"] != observation["error"]):
            raise ValueError("La memoria no coincide con la captura y consumo.")
        if entry["review"] is not None:
            reviewed = review_rules(_strict_json(entry["content"]), consumed, permit["data"]["observations"])
            if reviewed != entry["review"] or _strict_json(_read(directory / f"review-{number:02d}.json", 32768)) != reviewed:
                raise ValueError("La revisión técnica cambió.")
            if reviewed["eligible_for_experiment"]: consumed.add(reviewed["spec_sha256"])
        if entry["results"] is not None:
            result = entry["results"]
            view = _view(permit, entry["review"])
            calculation_id = sha256(_canonical(engine._identity(view))).hexdigest()
            comparison = entry["comparison"]
            expected_plan = {**view, "calculation_id": calculation_id, "comparison": comparison,
                             "criterion": permit["criterion"], "review": entry["review"], "context_sha256": metadata["sha256"]}
            if (completion["analysis"]["requires_stop"] or entry["error"] is not None
                    or not entry["review"]["eligible_for_experiment"] or comparison["operation_id"] != calculation_id
                    or comparison["proposal_id"] != entry["receipt"]["operation_id"] or comparison not in state["reservations"]
                    or result["policy"] != view["policy"] or result["data"] != view["data"]
                    or result["proposal"] != {"criterion": permit["criterion"]}
                    or _strict_json(_read(directory / f"plan-{number:02d}.json", 32768)) != expected_plan
                    or _strict_json(_read(directory / f"result-{number:02d}.json", 262144)) != result):
                raise ValueError("Resultados incompatibles con revisión, plan o recibo.")
            expected_files = {f"baseline-{number:02d}.json", f"candidate-{number:02d}.json", f"plan-{number:02d}.json"}
            if set(result["artifacts_sha256"]) != expected_files: raise ValueError("Contabilidad incompleta.")
            for name, digest in result["artifacts_sha256"].items():
                if sha256(_read(directory / name, 32 * 1024 * 1024)).hexdigest() != digest: raise ValueError("Contabilidad o plan alterados.")
            receipt_ids.add(comparison["receipt_id"])
            for role in ("baseline", "candidate"):
                computed = _strict_json(_read(directory / f"{role}-{number:02d}.json", 32 * 1024 * 1024))
                if computed["summary"] != result[role]: raise ValueError("El resumen cambió respecto a la contabilidad.")
            expected_raw = _canonical({"protocol": "local_cycle_calculation_v1", "identity": engine._identity(view),
                                      "run_dir": str(directory), "scope_id": permit["scope_id"],
                                      "request_sha256": entry["receipt"]["operation_id"], "code_sha256": _code_hashes()})
            if (_read(engine.ACCESS_ROOT / (calculation_id + ".json"), 262144) != expected_raw
                    or result["assessment"] != engine._assessment(result)):
                raise ValueError("La conclusión o reserva del motor cambió.")
        earlier.append(entry)
    if (receipt_ids != {item["receipt_id"] for item in state["reservations"]}
            or record["consumed_rule_identities"] != sorted(consumed)
            or record["usage"] != attempts.inspect_attempts(permit["scope_id"])):
        raise ValueError("La memoria omite reservas o consumo.")
    return record


def status(run_dir):
    directory = Path(run_dir).resolve()
    if (directory / "cycle.json").exists(): return inspect_cycle(directory)
    events = [_strict_json(line) for line in _read(directory / "events.jsonl", 4 * 1024 * 1024).splitlines()]
    if not events or events[0]["event"] != "cycle_started": raise ValueError("No es un intento de ciclo.")
    usage = None
    try:
        permit = verify_permit(Path(events[0]["data"]["permit_dir"]))
        usage = attempts.inspect_attempts(permit["scope_id"])
    except ERRORS: pass
    return {"schema_version": 1, "protocol": "incomplete_local_cycle_status_v1", "run_dir": str(directory),
            "status": "failed" if events[-1]["event"] == "cycle_failed" else "interrupted_or_in_progress",
            "last_recorded_event": events[-1], "usage": usage, "results_certified": False,
            "requires_stop": True, "retry_allowed": False, "new_model_requests": 0, "api_cost_usd": "0"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=f"{PROJECT_NAME} — ciclo local virtual acotado")
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--scope", required=True)
    prepare.add_argument("--output-dir", type=Path)
    run = commands.add_parser("run")
    run.add_argument("--permit", required=True, type=Path)
    run.add_argument("--allow-local-generation", action="store_true")
    run.add_argument("--allow-virtual-calculations", action="store_true")
    run.add_argument("--output-dir", type=Path)
    commands.add_parser("inspect").add_argument("--run", type=Path, required=True)
    commands.add_parser("status").add_argument("--run", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        with VerificationSession():
            kwargs = {"output_dir": args.output_dir} if getattr(args, "output_dir", None) else {}
            if args.command in ("inspect", "status"):
                print(json.dumps(inspect_cycle(args.run) if args.command == "inspect" else status(args.run), ensure_ascii=True))
                return
            if args.command == "prepare": result = prepare_cycle(args.scope, **kwargs)
            else: result = run_cycle(args.permit, allow_local_generation=args.allow_local_generation,
                                    allow_virtual_calculations=args.allow_virtual_calculations, **kwargs)
        print(result)
    except ERRORS as error: parser.exit(1, f"Ciclo detenido: {error}\n")


if __name__ == "__main__": main()
