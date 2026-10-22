"""Contratos de lectura para TiresIAs: registros históricos, cuentas y procedencia."""

from datetime import date
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import re
from functools import wraps

from trading_ai.lab_catalog import Catalog, ERRORS, identifier, origin_key


UNKNOWN = "No disponible"
LIMIT = ("Datos históricos conocidos del BCE, con referencias educativas y costes hipotéticos. "
         "No son cotizaciones actuales ni validación independiente. Las cuentas son virtuales e independientes.")
TITLES = {"known_walk_forward_result_v1": "Walk-forward sobre desarrollo conocido",
          "local_campaign_cycle_result_v1": "Ciclo local de investigación",
          "local_campaign_cycle_v1": "Ciclo local de investigación",
          "controlled_local_campaign_v1": "Ciclo local de investigación",
          "research": "Investigación SMA / EMA", "campaign-attempts": "Captura de propuesta",
          "campaign-memory": "Memoria de campaña", "structured-ideas": "Propuesta estructurada",
          "structured-revisions": "Reformulación registrada", "evaluations": "Evaluación histórica",
          "holdout": "Propuesta congelada", "discovery": "Idea de estrategia"}
TITLES.update({"robustness": "Sensibilidad y selección interna", "compact-history": "Memoria compacta",
               "chat-experiments": "Prueba histórica desde conversación",
               "compact-generations": "Intento compacto", "compact-candidates": "Candidata de reglas",
               "structured-sessions": "Sesión de revisión", "research-sessions": "Sesión de investigación",
               "structured-review-memory": "Memoria de revisiones", "structured-drafts": "Borrador de reglas",
               "formalization": "Traducción de una idea", "rule-reviews": "Revisión técnica",
               "rule-executions": "Intento de cálculo de reglas", "idea-revisions": "Revisión de una idea"})


def object_value(value):
    return value if isinstance(value, dict) else {}


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)): return False
    try: return Decimal(str(value)).is_finite()
    except InvalidOperation: return False


def public_file(entry):
    return {key: entry.get(key) for key in ("id", "path", "source", "expected_sha256", "sha256", "bytes")}


def usage_totals(items):
    """Una ausencia nunca se convierte en cero. Los subtotales no son un total histórico."""
    fields = ("model_requests", "input_tokens", "output_tokens", "api_cost_usd")
    if not isinstance(items, list) or not items:
        return {field: None for field in fields}
    result = {}
    for field in fields:
        values = [object_value(item).get(field) for item in items]
        if any(not finite(value) or Decimal(str(value)) < 0 for value in values):
            result[field] = None
        else:
            total = sum((Decimal(str(value)) for value in values), Decimal(0))
            result[field] = str(total) if field == "api_cost_usd" else int(total) if total == total.to_integral() else None
    return result


def operation(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        if not self._depth:
            self.catalog.begin_read()
            self._details, self._experiment_items = {}, None
        self._depth += 1
        try: return method(self, *args, **kwargs)
        finally: self._depth -= 1
    return call


class LabQuery:
    def __init__(self, root=None, *, catalog=None):
        self.catalog = catalog if catalog is not None else Catalog() if root is None else Catalog(root)
        self._depth = 0

    def _metadata(self, record, value, events):
        policy = object_value(value.get("policy") or value.get("reference_policy"))
        proposal = object_value(value.get("proposal") or value.get("seed_proposal"))
        args = object_value(proposal.get("arguments"))
        first = events[0] if events else {}
        policy = policy or object_value(object_value(first.get("data")).get("policy"))
        if not policy:
            try:
                context = self._context(record, value)
                policy = object_value(context.get("policy") or context.get("reference_policy"))
                if not args: args = object_value(object_value(context.get("seed_proposal")).get("arguments"))
            except ERRORS: pass
        last = events[-1] if events else {}
        state = value.get("stop_reason") or value.get("status") or value.get("stage") or last.get("event") or "incomplete"
        if record["missing_primary"]: state = "incomplete"
        protocol = value.get("protocol")
        title = proposal.get("title") or TITLES.get(str(protocol)) or TITLES.get(record["bucket"]) or record["bucket"]
        if record["bucket"].startswith(("research-check-", "sufficiency-check-", "consistency-check-")):
            title = "Comprobación histórica del investigador"
        strategy = args.get("strategy") or object_value(value.get("candidate")).get("strategy")
        if value.get("protocol") == "known_walk_forward_result_v1": strategy = "SMA / EMA · walk-forward"
        if not strategy and (value.get("spec") or value.get("entries")): strategy = "Reglas declarativas"
        return {"id": record["id"], "title": title, "kind": record["bucket"],
                "pair": policy.get("pair"), "strategy": strategy,
                "date": first.get("at"), "state": state, "origin": "archive" if record["archive"] else "local",
                "path": self.catalog.files[record["file"]]["path"],
                "integrity": "not_checked", "has_results": bool(value.get("baseline") or value.get("folds") or value.get("blocks") or value.get("development_result") or value.get("rows"))}

    @operation
    def experiments(self, filters=None):
        filters = filters or {}
        result, warnings = [], list(self.catalog.warnings)
        for record in self.catalog.records.values() if self._experiment_items is None else ():
            try:
                value, events = self.catalog.payload(record), self.catalog.events(record)
                item = self._metadata(record, value, events)
            except ERRORS as error:
                item = self._metadata(record, {}, [])
                item.update(state="unreadable", integrity="unverifiable", issue=str(error))
            result.append(item)
        if self._experiment_items is None: self._experiment_items = result
        result = []
        for item in self._experiment_items:
            if any(filters.get(key) and str(item.get(key) or "").casefold() != filters[key].casefold()
                   for key in ("pair", "origin", "state")): continue
            if filters.get("strategy") and filters["strategy"].casefold() not in str(item.get("strategy") or "").casefold(): continue
            if filters.get("date") and not str(item.get("date") or "").startswith(filters["date"]): continue
            if filters.get("q") and filters["q"].casefold() not in json.dumps(item, ensure_ascii=False).casefold(): continue
            result.append(item)
        result.sort(key=lambda item: (str(item["date"] or ""), item["path"]), reverse=True)
        return {"items": result, "warnings": warnings, "queried_at": self.catalog.queried_at, "limits": LIMIT}

    def _context(self, record, value):
        context = value
        if value.get("protocol") == "known_walk_forward_result_v1":
            context = self.catalog.linked(record, value.get("plan"), "plan.json") or {}
        elif value.get("protocol") == "local_campaign_cycle_result_v1" or "permit" in value:
            context = self.catalog.linked(record, value.get("permit"), "permit.json") or {}
        elif isinstance(value.get("plan"), dict) and "reference_policy" in value["plan"]:
            context = value["plan"]
        elif object_value(value.get("reference")).get("frozen_dir"):
            context = self.catalog.linked(record, {"directory": value["reference"]["frozen_dir"]}, "frozen.json") or value
        return context

    @operation
    def detail(self, key):
        if key in self._details: return self._details[key]
        if key not in self.catalog.records: raise KeyError("Experimento no catalogado.")
        record = self.catalog.records[key]
        warnings = []
        try: value = self.catalog.payload(record)
        except ERRORS as error:
            value = {}
            warnings.append("Registro no legible: " + str(error))
        try: events = self.catalog.events(record)
        except ERRORS as error:
            events = []
            warnings.append("Eventos no legibles: " + str(error))
        try: integrity = self.catalog.integrity(record)
        except ERRORS as error:
            integrity = {"state": "unverifiable", "label": "Fuente no verificable", "reason": str(error)}
        try: context = self._context(record, value)
        except ERRORS as error:
            context = {}
            warnings.append("Referencia no disponible: " + str(error))
        policy = object_value(context.get("policy") or context.get("reference_policy"))
        if not policy:
            policy = object_value(object_value(events[0].get("data")).get("policy")) if events else {}
        data = object_value(context.get("data") or context.get("source"))
        proposal = object_value(value.get("proposal") or context.get("seed_proposal"))
        metadata = self._metadata(record, value, events)
        if policy.get("pair"): metadata["pair"] = policy["pair"]
        # Contenido original y descripciones Python se mantienen separados.
        model = [{"at": event.get("at"), "stage": object_value(event.get("data")).get("stage"),
                  "content": object_value(event.get("data")).get("content"),
                  "usage": object_value(event.get("data")).get("usage")}
                 for event in events if event["event"] == "model_response"]
        python = []
        for entry in value.get("entries", []) if isinstance(value.get("entries"), list) else []:
            if not isinstance(entry, dict): continue
            if "content" in entry: model.append({"content": entry["content"], "usage": entry.get("usage")})
            if entry.get("review"): python.append(entry["review"])
        if value.get("rule_description"): python.append(value["rule_description"])
        if "observation.raw" in record["files"]:
            try:
                from trading_ai.formalization import _strict_json
                observation = _strict_json(self.catalog.file(record["files"]["observation.raw"])[1])
                if isinstance(observation, dict) and "content" in observation:
                    model.append({"content": observation["content"], "origin": object_value(value.get("analysis")).get("observation_origin")})
            except ERRORS as error: warnings.append("Captura original no legible: " + str(error))
        try: accounts = self._accounts(record, value, context, policy, data)
        except ERRORS as error:
            accounts = []
            warnings.append("Resultados incompletos o incompatibles: " + str(error))
        current = None
        if not record["archive"] and isinstance(value.get("scope_id"), str):
            # El lector existente usa SQLite mode=ro y query_only, sin inicializarlo.
            from trading_ai import campaign_ledger
            if self.catalog.root == campaign_ledger.ROOT.resolve():
                try:
                    self.catalog.safe(campaign_ledger.LEDGER_PATH)
                    current = campaign_ledger.inspect_campaign(value["scope_id"])
                except ERRORS as error:
                    current = {"status": "unverifiable", "reason": str(error)}
        related = {}
        primary = self.catalog.files[record["file"]]
        origin = origin_key(primary["source"]) or primary["path"]
        for file in self.catalog.files.values():
            if file["archive"] and origin_key(file["source"]) == origin:
                manifest = self.catalog.files[file["archive"]]
                related[manifest["id"]] = public_file(manifest)
                report_path = manifest["path"].rsplit("/", 1)[0] + ".md"
                for report in self.catalog.files.values():
                    if report["path"] == report_path: related[report["id"]] = public_file(report)
        conclusion = value.get("assessment")
        conclusion_origin = "python" if conclusion else None
        if not conclusion and events:
            final = object_value(events[-1].get("data"))
            conclusion = final.get("assessment")
            conclusion_origin = object_value(final.get("analysis_origin")).get("source")
        errors = [{"at": event.get("at"), "event": event["event"], "data": event.get("data")}
                  for event in events if any(word in event["event"] for word in ("failed", "error", "reject", "duplicate"))]
        result = {**metadata, "queried_at": self.catalog.queried_at, "integrity": integrity,
                "recorded_state_notice": "Estado del registro guardado; no indica un proceso activo ni concede permiso de ejecución.",
                "policy": policy, "data": data, "proposal": proposal,
                "hypothesis": proposal.get("hypothesis"), "criterion": proposal.get("criterion") or context.get("criterion"),
                "rules": value.get("spec") or object_value(value.get("candidate")).get("spec"),
                "assessment": conclusion, "assessment_origin": conclusion_origin, "model": model, "python": python, "errors": errors,
                "events": [{"at": event.get("at"), "event": event["event"],
                            "data": {k: v for k, v in object_value(event.get("data")).items() if k not in ("messages", "schema")}}
                           for event in events],
                "accounts": accounts, "usage": self._usage(value, events), "current_ledger": current,
                "results_certified": False,
                "record": value, "warnings": warnings,
                "files": [public_file(self.catalog.files[file]) for file in record["files"].values()],
                "evidence": list(related.values()),
                "manifest": public_file(self.catalog.files[record["archive"]]) if record["archive"] else None,
                "limits": LIMIT}
        self._details[key] = result
        return result

    def _accounts(self, record, value, context, policy, data):
        accounts = []
        if isinstance(value.get("development_result"), dict):
            value = value["development_result"]
            data = object_value(value.get("source"))

        def add(label, summary, block, filename=None, parameters=None, account_policy=None):
            if not isinstance(summary, dict): return
            key = identifier(record["id"] + label)
            source = record["files"].get(filename) if filename else None
            accounts.append({"id": key, "experiment": record["id"], "label": label,
                             "summary": summary, "policy": account_policy or policy, "data": block,
                             "parameters": parameters or {}, "file": source,
                             "details_available": source is not None,
                             "currency": summary.get("quote_currency"), "pair": (account_policy or policy).get("pair"),
                             "independent_account": True})

        if value.get("protocol") == "known_walk_forward_result_v1":
            candidates = {item["id"]: item for item in context.get("candidates", [])}
            folds = {item["index"]: item for item in context.get("folds", [])}
            base = {"strategy": policy.get("baseline_strategy"), "fast_window": policy.get("fast_window"), "slow_window": policy.get("slow_window")}
            for fold in value.get("folds", []):
                index = fold["index"]
                block = folds.get(index, {})
                add(f"Ventana {index} · entrenamiento · base", fold.get("train_baseline"), block.get("train", {}), f"train-{index:02d}-baseline.json", base)
                for candidate, summary in object_value(fold.get("train_candidates")).items():
                    add(f"Ventana {index} · entrenamiento · {summary.get('strategy', candidate)}", summary, block.get("train", {}), f"train-{index:02d}-{candidate}.json", candidates.get(candidate))
                check = object_value(fold.get("check"))
                for role, suffix in (("baseline", "baseline"), ("candidate", fold.get("selected_id"))):
                    if check.get(role):
                        add(f"Ventana {index} · comprobación · {role}", check[role], block.get("check", {}), f"check-{index:02d}-{suffix}.json", base if role == "baseline" else candidates.get(suffix))
        elif isinstance(value.get("rows"), dict):
            for period, rows in value["rows"].items():
                for row in rows:
                    result = row["result"]
                    for role in ("baseline", "candidate"):
                        args = object_value(object_value(result.get("proposal")).get("arguments")) if role == "candidate" else {
                            "strategy": result["policy"].get("baseline_strategy"), "fast_window": result["policy"].get("fast_window"), "slow_window": result["policy"].get("slow_window")}
                        add(f"{period} · {row['scenario']['id']} · {role}", result[role], result["source"], parameters=args, account_policy=result["policy"])
        elif isinstance(value.get("blocks"), dict):
            for name, block in value["blocks"].items():
                results = object_value(object_value(block).get("results")) or object_value(block)
                for role in ("baseline", "candidate"):
                    parameters = object_value(object_value(results.get("proposal")).get("arguments")) if role == "candidate" else {
                        "strategy": policy.get("baseline_strategy"), "fast_window": policy.get("fast_window"), "slow_window": policy.get("slow_window")}
                    add(f"{name} · {role}", results.get(role), results.get("source", {}), parameters=parameters)
        else:
            for role in ("baseline", "candidate"):
                parameters = (object_value(object_value(value.get("proposal")).get("arguments")) if role == "candidate" else
                              {"strategy": policy.get("baseline_strategy"), "fast_window": policy.get("fast_window"), "slow_window": policy.get("slow_window")})
                add(role, value.get(role), data, role + ".json", parameters)
        return accounts

    @operation
    def account(self, experiment, key):
        detail = self.detail(experiment)
        account = next((item for item in detail["accounts"] if item["id"] == key), None)
        if account is None: raise KeyError("Cuenta no catalogada.")
        result = {**account, "integrity": detail["integrity"], "backtest": None, "warnings": list(detail["warnings"])}
        code = detail["record"].get("code_sha256")
        if not code and detail["events"]: code = object_value(detail["events"][0].get("data")).get("engine_sha256")
        result["execution_identity"] = identifier(json.dumps({"code": code, "execution": detail["record"].get("execution_policy")}, sort_keys=True)) if code else None
        if account["file"]:
            try:
                entry, raw = self.catalog.file(account["file"])
                # Cotejar el detalle, además del resumen: una operación alterada no pasa por coincidir los totales.
                expected = object_value(detail["record"].get("artifacts_sha256")).get(entry["path"].rsplit("/", 1)[-1])
                archived = {file["expected_sha256"] for file in self.catalog.files.values()
                            if file["archive"] and origin_key(file["source"]) == entry["path"]}
                if ((entry["expected_sha256"] and entry["sha256"] != entry["expected_sha256"])
                        or expected and entry["sha256"] != expected
                        or archived and entry["sha256"] not in archived):
                    raise ValueError("La contabilidad no conserva su huella registrada.")
                from trading_ai.formalization import _strict_json
                value = _strict_json(raw)
                if not isinstance(value, dict) or value.get("summary") != account["summary"] or not isinstance(value.get("backtest"), dict):
                    raise ValueError("El detalle no coincide con el resumen guardado.")
                backtest = value["backtest"]
                points, trades = backtest.get("equity_curve"), backtest.get("closed_trades")
                if (not isinstance(points, list) or not 0 < len(points) <= 25000 or not isinstance(trades, list) or len(trades) > 10000
                        or backtest.get("pair") != account["pair"] or backtest.get("quote_currency") != account["currency"]):
                    raise ValueError("Contabilidad incompleta o cuenta incompatible.")
                if any(backtest.get(field) != account["policy"].get(field) for field in ("initial_capital", "cost_rate", "allocation_fraction")):
                    raise ValueError("Los controles de la cuenta difieren del registro.")
                previous = None
                for point in points:
                    day = date.fromisoformat(point["date"])
                    if previous and day <= previous: raise ValueError("Fechas de curva incompatibles.")
                    if any(not finite(point.get(field)) for field in ("equity", "cash", "position_value", "drawdown", "drawdown_percent")):
                        raise ValueError("Curva con importes no finitos o ausentes.")
                    previous = day
                for trade in trades:
                    position = trade["position"]
                    for field in ("entry_signal_date", "entry_date"): date.fromisoformat(position[field])
                    for field in ("exit_signal_date", "exit_date"): date.fromisoformat(trade[field])
                    if (any(not finite(position.get(field)) for field in ("quantity", "entry_price", "entry_cost"))
                            or any(not finite(trade.get(field)) for field in ("exit_price", "exit_cost", "pnl"))):
                        raise ValueError("Operación incompleta o con importes no finitos.")
                if (len(trades) != account["summary"].get("closed_trades")
                        or points[-1]["equity"] != account["summary"].get("final_equity")
                        or account["data"].get("first_date", points[0]["date"]) != points[0]["date"]
                        or account["data"].get("last_date", points[-1]["date"]) != points[-1]["date"]):
                    raise ValueError("Fechas, capital final o número de operaciones incompatibles con el resumen.")
                result.update(backtest=backtest, file=public_file(entry))
            except ERRORS as error:
                result["warnings"].append("Detalle no verificable: " + str(error))
                result["integrity"] = {"state": "unverifiable", "label": "Contabilidad no verificable"}
        return result

    @operation
    def compare(self, left_experiment, left_account, right_experiment, right_account):
        left, right = self.account(left_experiment, left_account), self.account(right_experiment, right_account)
        differences = []
        for key in ("pair", "currency"):
            if not left.get(key) or left[key] != right.get(key): differences.append(key)
        for area, fields in (("data", ("sha256", "first_date", "last_date")),
                             ("policy", ("initial_capital", "cost_rate", "allocation_fraction"))):
            for field in fields:
                a, b = left[area].get(field), right[area].get(field)
                known = field in left[area] and field in right[area] and (a is not None or field == "allocation_fraction")
                if not known or a != b: differences.append(f"{area}.{field}")
        for account in (left, right):
            if account["integrity"]["state"] in ("changed", "unverifiable", "incomplete"):
                differences.append("integrity")
            if any(not finite(account["summary"].get(field)) for field in ("final_equity", "return_percent", "max_drawdown_percent")):
                differences.append("summary")
            policy, data = account["policy"], account["data"]
            if (not finite(policy.get("initial_capital")) or Decimal(str(policy["initial_capital"])) <= 0
                    or not finite(policy.get("cost_rate")) or not 0 <= Decimal(str(policy["cost_rate"])) < 1
                    or policy.get("allocation_fraction") is not None and
                    (not finite(policy["allocation_fraction"]) or not 0 < Decimal(str(policy["allocation_fraction"])) <= 1)):
                differences.append("invalid_policy")
            try:
                if date.fromisoformat(data["first_date"]) > date.fromisoformat(data["last_date"]): raise ValueError
                if re.fullmatch(r"[0-9a-f]{64}", data["sha256"]) is None: raise ValueError
            except (KeyError, TypeError, ValueError): differences.append("invalid_data_identity")
        if left_experiment != right_experiment and (not left["execution_identity"] or left["execution_identity"] != right["execution_identity"]):
            differences.append("execution_identity_unknown_or_different")
        if left["id"] == right["id"]: differences.append("same_account")
        return {"compatible": not differences, "differences": sorted(set(differences)),
                "strategy_differences": {"left": left["parameters"], "right": right["parameters"]},
                "accounts": [{key: account[key] for key in ("id", "label", "currency", "pair", "summary", "data", "policy", "integrity")}
                             for account in (left, right)],
                "notice": "Comparación descriptiva de cuentas independientes. No se suman capitales ni se componen rentabilidades."}

    def _usage(self, value, events):
        usage = value.get("usage")
        if usage is None: usage = object_value(value.get("analysis")).get("usage")
        inherited = value.get("inherited_usage") or []
        if isinstance(usage, dict) and "usage" in usage:
            inherited = usage.get("inherited_usage") or inherited
            new = object_value(usage.get("usage"))
            subtotals = usage.get("known_subtotals")
        else:
            items = usage if isinstance(usage, list) else [usage] if isinstance(usage, dict) else []
            if not items:
                items = [object_value(event.get("data")).get("usage") for event in events if event["event"] == "model_response"]
            new = usage_totals(items)
            subtotals = None
            # Campos explícitos del registro final: no se infieren ceros de listas vacías.
            final = object_value(events[-1].get("data")) if events and events[-1]["event"] in ("run_completed", "run_failed") else {}
            for field in ("model_requests", "api_cost_usd"):
                explicit = value.get(field, final.get(field))
                if finite(explicit) and Decimal(str(explicit)) >= 0: new[field] = explicit
        return {"new": {field: new.get(field) for field in ("model_requests", "input_tokens", "output_tokens", "api_cost_usd")},
                "inherited": inherited, "known_subtotals": subtotals,
                "scope": "Consumo registrado en esta fuente; puede solaparse con otras memorias o copias. No es el total de la aplicación."}

    @operation
    def consumption(self):
        items, seen = [], set()
        # Preferir registros locales; las copias de una misma fuente no se vuelven a contar.
        records = sorted(self.catalog.records.values(), key=lambda item: bool(item["archive"]))
        for record in records:
            file = self.catalog.files[record["file"]]
            origin = origin_key(file["source"]) or file["path"]
            if origin in seen: continue
            seen.add(origin)
            try:
                value, events = self.catalog.payload(record), self.catalog.events(record)
                usage = self._usage(value, events)
                if any(x is not None for x in usage["new"].values()) or usage["inherited"] or events:
                    items.append({**self._metadata(record, value, events), **usage})
            except ERRORS as error:
                items.append({"id": record["id"], "path": file["path"], "issue": str(error),
                              "new": usage_totals([]), "inherited": []})
        return {"items": items, "queried_at": self.catalog.queried_at,
                "notice": "Sin total global: hay memorias solapadas. Desconocido no equivale a cero; una reserva no acredita una consulta enviada."}

    @operation
    def home(self):
        experiments = self.experiments()
        return {"name": "TiresIAs", "queried_at": self.catalog.queried_at,
                "counts": {"experiments": len(experiments["items"]), "archives": len(self.catalog.archives),
                           "local": sum(item["origin"] == "local" for item in experiments["items"])},
                "recent": experiments["items"][:5], "warnings": experiments["warnings"], "limits": LIMIT,
                "reports": [public_file(file) for file in self.catalog.files.values()
                            if file["path"].count("/") == 1 and file["path"].endswith(".md")]}

    @operation
    def overviews(self):
        return {"experiments": self.experiments(), "home": self.home(), "consumption": self.consumption()}
