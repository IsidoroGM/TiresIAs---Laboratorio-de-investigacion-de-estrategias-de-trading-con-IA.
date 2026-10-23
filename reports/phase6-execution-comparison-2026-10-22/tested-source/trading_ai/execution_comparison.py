"""Compare supplied execution CSVs with frozen BID/ASK runs, without account effects.

Column meanings, units, timezone and tolerances are declared, never guessed.
Neither a matching CSV nor a user's declaration authenticates an external engine.
"""

from collections import defaultdict
from datetime import date, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from itertools import islice
import csv
import io
from pathlib import Path
from uuid import uuid4

from trading_ai.dukascopy_service import DukascopyResearch
from trading_ai.tv_contracts import canonical, checksum, decimal_text, fields, hash_id, number, safe_under, strict_json
from trading_ai.tv_io import parse_numeric, parse_time


PROTOCOL = "tiresias_execution_comparison_v1"
COLUMNS = ("external_id", "executed_at", "side", "quantity", "price", "fee", "signal_at")
OPTIONAL = ("external_id", "fee", "signal_at")
META = ("pair", "currency", "strategy", "fast", "slow", "start_date", "end_date_exclusive", "sessions_sha256")
POLICY = {"price_tolerance": "0", "quantity_tolerance": "0", "fee_tolerance": "0", "time_tolerance_seconds": 0, "alignment_window_seconds": 0}


def mapping_template():
    return {"protocol": "tiresias_external_execution_csv_v1", "columns": {key: key for key in COLUMNS},
            "delimiter": ",", "decimal_separator": ".", "grouping_separator": None,
            "sides": {"buy": "buy", "sell": "sell"}, "time_format": "iso8601", "quantity_multiplier": "1"}


def declaration_template():
    return {"producer": "", "origin": "user_supplied_external", **{key: None for key in META}}


def validate_mapping(value):
    fields(value, mapping_template(), "mapa de contraste")
    fields(value["columns"], COLUMNS, "columnas de contraste")
    if value["protocol"] != "tiresias_external_execution_csv_v1": raise ValueError("Versión de mapa incompatible.")
    names = []
    for key, name in value["columns"].items():
        if name is None and key in OPTIONAL: continue
        if not isinstance(name, str) or not 1 <= len(name) <= 80: raise ValueError("Columna requerida o nombre incompatible.")
        names.append(name)
    if len(names) != len(set(names)): raise ValueError("No reutilices columnas para significados distintos.")
    if value["delimiter"] not in (",", ";", "\t") or value["decimal_separator"] not in (".", ","):
        raise ValueError("Separadores incompatibles.")
    if value["grouping_separator"] not in (None, ".", ",", " ") or value["grouping_separator"] == value["decimal_separator"]:
        raise ValueError("Separador de miles ambiguo.")
    if value["time_format"] not in ("iso8601", "unix_ms", "utc_ymd_hm", "utc_dmy_hm"):
        raise ValueError("Declara ISO con zona o un formato UTC admitido; no se adivina la zona.")
    if (not isinstance(value["sides"], dict) or not 1 <= len(value["sides"]) <= 20
            or any(not isinstance(key, str) or not 1 <= len(key) <= 50 or side not in ("buy", "sell") for key, side in value["sides"].items())):
        raise ValueError("Acciones no declaradas.")
    number(value["quantity_multiplier"], "multiplicador de unidades base", maximum=Decimal("1e9"), positive=True)
    return value


def normalize_csv(raw, mapping):
    validate_mapping(mapping)
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= 2*1024*1024: raise ValueError("CSV entre 1 byte y 2 MiB requerido.")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""), delimiter=mapping["delimiter"], strict=True)
    headers = reader.fieldnames
    if headers is None or len(headers) != len(set(headers)) or any(name not in headers for name in mapping["columns"].values() if name is not None):
        raise ValueError("Columnas ausentes o duplicadas; revisa el archivo y su mapa.")
    rows, errors, identities = [], [], set()
    for line, source in enumerate(reader, 2):
        if line > 1001: raise ValueError("Máximo 1000 ejecuciones por informe.")
        try:
            if None in source or any(value is None for value in source.values()): raise ValueError("Fila CSV desalineada.")
            value = {key: None if name is None else source[name].strip() for key, name in mapping["columns"].items()}
            if value["side"] not in mapping["sides"]: raise ValueError("Acción no declarada.")
            external_id = value["external_id"] or None
            if external_id is not None:
                if len(external_id) > 128 or external_id in identities: raise ValueError("Identidad duplicada o excesiva.")
                identities.add(external_id)
            with localcontext(Context(prec=100)):
                quantity = Decimal(parse_numeric(value["quantity"], mapping))*Decimal(mapping["quantity_multiplier"])
            quantity = decimal_text(number(decimal_text(quantity), "cantidad en unidades base", maximum=Decimal("1e9"), positive=True))
            price = decimal_text(number(parse_numeric(value["price"], mapping), "precio", positive=True))
            fee = None if not value["fee"] else decimal_text(Decimal(parse_numeric(value["fee"], mapping)))
            rows.append({"line": line, "external_id": external_id, "side": mapping["sides"][value["side"]],
                "executed_at": parse_time(value["executed_at"], mapping["time_format"]), "quantity": quantity, "price": price,
                "fee": fee, "signal_at": None if not value["signal_at"] else parse_time(value["signal_at"], mapping["time_format"])})
        except (ValueError, TypeError, OverflowError) as error: errors.append({"line": line, "reason": str(error)})
    return {"rows": rows, "errors": errors}


def policy(value):
    fields(value, POLICY, "tolerancias")
    result = dict(value)
    for key in ("price_tolerance", "quantity_tolerance", "fee_tolerance"):
        result[key] = decimal_text(number(value[key], key, maximum=Decimal("1")))
    for key in ("time_tolerance_seconds", "alignment_window_seconds"):
        if type(value[key]) is not int or not 0 <= value[key] <= 86400: raise ValueError("Ventana temporal entre cero y un día requerida.")
    if value["time_tolerance_seconds"] > value["alignment_window_seconds"]: raise ValueError("La tolerancia temporal supera la ventana de alineación.")
    return result


def declaration(value):
    fields(value, declaration_template(), "declaración de origen")
    if not isinstance(value["producer"], str) or not 1 <= len(value["producer"].strip()) <= 120:
        raise ValueError("Identifica el productor del informe o ejemplo.")
    if value["origin"] not in ("user_supplied_external", "synthetic_fixture", "python_reexport"):
        raise ValueError("Origen no admitido.")
    for key in ("pair", "currency", "strategy"):
        if value[key] is not None and (not isinstance(value[key], str) or not 1 <= len(value[key]) <= 40): raise ValueError("Metadatos incompatibles.")
    for key in ("fast", "slow"):
        if value[key] is not None and (type(value[key]) is not int or not 1 <= value[key] <= 252): raise ValueError("Ventanas declaradas incompatibles.")
    for key in ("start_date", "end_date_exclusive"):
        if value[key] is not None and (not isinstance(value[key], str) or date.fromisoformat(value[key]).isoformat() != value[key]): raise ValueError("Fecha declarada incompatible.")
    if value["sessions_sha256"] is not None: hash_id(value["sessions_sha256"])
    if value["fast"] is not None and value["slow"] is not None and value["fast"] >= value["slow"]:
        raise ValueError("Ventanas declaradas fuera de orden.")
    if value["start_date"] is not None and value["end_date_exclusive"] is not None and value["start_date"] >= value["end_date_exclusive"]:
        raise ValueError("Período declarado fuera de orden.")
    return value


def seconds(a, b):
    return (datetime.fromisoformat(a.replace("Z", "+00:00"))-datetime.fromisoformat(b.replace("Z", "+00:00"))).total_seconds()


def compare(reference, normalized, settings, declared):
    expected = [{"index": index+1, "side": row["side"], "executed_at": row["executed_at"],
                 "signal_at": row["signal_at"], "quantity": row["quantity"], "price": row["price"],
                 "fee": row["assumed_commission"]} for index, row in enumerate(reference["hypothetical_fills"])]
    actual = normalized["rows"]
    config, source = reference["configuration"], reference["source"]
    expected_meta = {key: config[key] for key in ("pair", "currency", "strategy", "fast", "slow")}
    expected_meta.update(start_date=source.get("start_date"), end_date_exclusive=source.get("end_date_exclusive"), sessions_sha256=reference["sessions_sha256"])
    meta_unknown = [key for key in META if declared[key] is None or expected_meta[key] is None]
    meta_differences = [{"field": key, "python": expected_meta[key], "declared": declared[key]} for key in META
                        if key not in meta_unknown and declared[key] != expected_meta[key]]
    result = {"reference_rows": len(expected), "external_rows": len(actual), "pairs": [], "missing": [], "extra": [],
              "ambiguous": [], "metadata_differences": meta_differences, "metadata_unknown": meta_unknown,
              "reference_metadata": expected_meta, "errors": normalized["errors"], "unknown_fields": []}
    if normalized["errors"]:
        result["status"] = "invalid_report"
        return result
    left, right = set(range(len(expected))), set(range(len(actual)))
    paired = []
    # Match only mutual unique candidates. Missing rows never shift all later pairs.
    for window in sorted(set((0, settings["alignment_window_seconds"]))):
        choices = {i: [j for j in right if expected[i]["side"] == actual[j]["side"]
                       and abs(seconds(actual[j]["executed_at"], expected[i]["executed_at"])) <= window] for i in sorted(left)}
        owners = defaultdict(list)
        for i, candidates in choices.items():
            for j in candidates: owners[j].append(i)
        for i, candidates in choices.items():
            if len(candidates) == 1 and len(owners[candidates[0]]) == 1:
                j = candidates[0]; paired.append((i, j)); left.remove(i); right.remove(j)
    for i in sorted(left):
        candidates = [actual[j]["line"] for j in sorted(right) if expected[i]["side"] == actual[j]["side"]
                      and abs(seconds(actual[j]["executed_at"], expected[i]["executed_at"])) <= settings["alignment_window_seconds"]]
        if candidates: result["ambiguous"].append({"reference_index": expected[i]["index"], "external_lines": candidates})
    result["missing"] = [expected[i] for i in sorted(left)]
    result["extra"] = [actual[j] for j in sorted(right)]
    for i, j in sorted(paired):
        a, b = expected[i], actual[j]
        differences, unknown = [], []
        delta = seconds(b["executed_at"], a["executed_at"])
        if abs(delta) > settings["time_tolerance_seconds"]:
            differences.append({"field": "executed_at", "python": a["executed_at"], "external": b["executed_at"], "external_minus_python_seconds": delta})
        for field in ("quantity", "price", "fee"):
            if b[field] is None: unknown.append(field); continue
            with localcontext(Context(prec=100)): difference = Decimal(b[field])-Decimal(a[field])
            if difference.copy_abs() > Decimal(settings[field+"_tolerance"]):
                differences.append({"field": field, "python": a[field], "external": b[field], "external_minus_python": decimal_text(difference)})
        if b["signal_at"] is None: unknown.append("signal_at")
        elif a["signal_at"] != b["signal_at"]: differences.append({"field": "signal_at", "python": a["signal_at"], "external": b["signal_at"]})
        result["pairs"].append({"reference": a, "external": b, "differences": differences, "unknown_fields": unknown})
    result["unknown_fields"] = sorted(set(key for pair in result["pairs"] for key in pair["unknown_fields"]))
    if meta_differences: status = "incompatible_configuration"
    elif result["missing"] or result["extra"] or any(pair["differences"] for pair in result["pairs"]): status = "differences"
    elif not expected: status = "inconclusive_no_fills"
    elif result["unknown_fields"] or meta_unknown: status = "incomplete_evidence"
    else: status = "matching_fields_unverified_origin"
    result["status"] = status
    return result


class ExecutionComparisons:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.directory = safe_under(self.root, ".local", "execution-comparisons")

    def prepare(self, *, run, raw, name, mapping, tolerances, metadata):
        if not isinstance(name, str) or not 1 <= len(name) <= 120 or any(char in name for char in '/\\\x00\r\n:'):
            raise ValueError("Nombre simple de informe requerido.")
        settings, declared = policy(tolerances), declaration(metadata)
        reference = DukascopyResearch(self.root).get(run)
        if reference["status"] != "simulated": raise ValueError("Elige una simulación con histórico suficiente y sin huecos bloqueantes.")
        normalized = normalize_csv(raw, mapping)
        result = {"protocol": PROTOCOL, "reference_run": run, "reference_sha256": reference["result_sha256"],
            "csv_sha256": sha256(raw).hexdigest(), "file_name": name, "mapping": mapping, "policy": settings,
            "declaration": declared, "comparison": compare(reference, normalized, settings, declared),
            "normalized_external": normalized, "external_origin_verified": False, "external_format_verified": False,
            "external_equivalence_verified": False, "accounting_processed": False, "external_orders_sent": False,
            "notice": "Contraste de campos declarados; no autentica el origen ni demuestra equivalencia externa. Ninguna cuenta se modifica."}
        return result, reference

    def preview(self, **values):
        result, _ = self.prepare(**values)
        return {"preview": result, "approval_sha256": checksum(result)}

    def save(self, *, approval_sha256, **values):
        result, _ = self.prepare(**values)
        identity = checksum(result)
        if identity != approval_sha256: raise ValueError("El informe, fuente o controles cambiaron; revisa otra vista previa.")
        target = safe_under(self.directory, identity)
        if target.exists(): self.get(identity); return {"id": identity, "created": False}
        self.directory.mkdir(parents=True, exist_ok=True)
        if len(list(islice(self.directory.iterdir(), 101))) >= 100: raise ValueError("Límite de cien comparaciones de ejecuciones.")
        temporary = safe_under(self.directory, "preparing-"+uuid4().hex)
        temporary.mkdir()
        original = safe_under(self.root, ".local", "dukascopy-research", result["reference_run"])
        contents = {"original.csv": values["raw"], "comparison.json": canonical(result)}
        for name in ("simulation.json", "input-manifest.json", "input-daily.json"):
            contents["reference-"+name] = safe_under(original, name).read_bytes()
        # Verify again after copying, without recalculating the strategy.
        if strict_json(contents["reference-simulation.json"])["result_sha256"] != result["reference_sha256"]:
            raise ValueError("La referencia cambió al copiar; no se publica el contraste.")
        summary = {"id": identity, "status": result["comparison"]["status"], "reference_run": result["reference_run"],
                   "file_name": result["file_name"], "origin": result["declaration"]["origin"], "inputs_verified_now": False}
        contents["summary.json"] = canonical(summary)
        manifest = {"protocol": PROTOCOL, "id": identity, "evidence_sha256": {name: sha256(raw).hexdigest() for name, raw in contents.items()}}
        for name, raw in {**contents, "manifest.json": canonical(manifest)}.items():
            with safe_under(temporary, name).open("xb") as stream: stream.write(raw)
        self._load(temporary, identity)
        try: temporary.rename(target)
        except FileExistsError:
            self.get(identity)
            return {"id": identity, "created": False}
        return {"id": identity, "created": True}

    @staticmethod
    def _load(directory, identity):
        from trading_ai.dukascopy_backtest import read_bounded
        manifest = strict_json(read_bounded(safe_under(directory, "manifest.json"), 65536))
        expected = {"original.csv", "comparison.json", "summary.json", "reference-simulation.json", "reference-input-manifest.json", "reference-input-daily.json"}
        if (not isinstance(manifest, dict) or manifest.get("protocol") != PROTOCOL or manifest.get("id") != identity
                or not isinstance(manifest.get("evidence_sha256"), dict) or set(manifest["evidence_sha256"]) != expected):
            raise ValueError("Manifiesto de contraste incompatible.")
        raw_files = {name: read_bounded(safe_under(directory, name), 8*1024*1024) for name in expected}
        if any(sha256(raw_files[name]).hexdigest() != value for name, value in manifest["evidence_sha256"].items()):
            raise ValueError("El original o alguna evidencia de contraste fue alterada.")
        result = strict_json(raw_files["comparison.json"])
        if checksum(result) != identity: raise ValueError("El contraste no coincide con su identidad.")
        reference = strict_json(raw_files["reference-simulation.json"])
        DukascopyResearch.validate_result(reference)
        if reference["result_sha256"] != result["reference_sha256"] or sha256(raw_files["original.csv"]).hexdigest() != result["csv_sha256"]:
            raise ValueError("Entradas distintas de las revisadas.")
        for filename, key in (("reference-input-manifest.json", "manifest_sha256"), ("reference-input-daily.json", "daily_file_sha256")):
            if sha256(raw_files[filename]).hexdigest() != reference["source"][key]: raise ValueError("Copia de precios incompatible con la referencia.")
        return result

    def get(self, identity): return self._load(safe_under(self.directory, hash_id(identity)), identity)

    def overview(self):
        values, warnings = [], []
        if self.directory.exists():
            entries = list(islice(self.directory.iterdir(), 201))
            if len(entries) > 200: warnings.append("Catálogo limitado a 200 entradas.")
            for path in sorted(entries[:200]):
                if path.name.startswith("preparing-"): warnings.append("Preparación de contraste incompleta conservada."); continue
                try:
                    hash_id(path.name)
                    summary_path = safe_under(self.directory, path.name, "summary.json")
                    if summary_path.stat().st_size > 65536: raise ValueError("Resumen excesivo.")
                    summary_raw = summary_path.read_bytes()
                    summary = strict_json(summary_raw)
                    if not isinstance(summary, dict) or summary.get("id") != path.name: raise ValueError("Identidad de resumen incompatible.")
                    from trading_ai.dukascopy_backtest import read_bounded
                    manifest = strict_json(read_bounded(safe_under(path, "manifest.json"), 65536))
                    if (not isinstance(manifest, dict) or manifest.get("protocol") != PROTOCOL or manifest.get("id") != path.name
                            or not isinstance(manifest.get("evidence_sha256"), dict)
                            or manifest["evidence_sha256"].get("summary.json") != sha256(summary_raw).hexdigest()):
                        raise ValueError("Resumen alterado.")
                    summary["inputs_verified_now"] = False
                    values.append(summary)
                except (ValueError, OSError, KeyError, TypeError) as error: warnings.append(path.name+": "+str(error))
        return {"comparisons": values, "warnings": warnings, "metadata_only": True}
