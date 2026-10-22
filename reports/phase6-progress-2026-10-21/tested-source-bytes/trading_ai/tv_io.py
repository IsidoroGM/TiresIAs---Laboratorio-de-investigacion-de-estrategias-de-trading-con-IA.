"""Paquetes locales e importación con mapa de columnas explícito, sin adivinar CSV."""

from datetime import UTC, datetime, timedelta
from contextlib import contextmanager
from hashlib import sha256
import csv
import io
import os
from pathlib import Path
import re
from uuid import uuid4

from trading_ai.tv_contracts import (canonical, checksum, fields, hash_id, instant, number,
                                     safe_under, strict_json, validate_contract, validate_fill)
from trading_ai.tv_pine import verify_bundle, write_bundle


COLUMNS = ("execution_id", "sequence", "side", "quantity", "price", "fee", "signal_at", "executed_at")


class BundleRepository:
    def __init__(self, root): self.root = Path(root).resolve()

    def create(self, contract):
        contract = validate_contract(contract)
        identity = checksum(contract)
        parent = safe_under(self.root, ".local", "tradingview-bundles")
        target = safe_under(self.root, ".local", "tradingview-bundles", identity)
        if target.exists():
            if self.get(identity)["contract"] != contract: raise ValueError("El paquete existente es diferente.")
            return {"id": identity, "created": False}
        parent.mkdir(parents=True, exist_ok=True)
        if len(list(parent.iterdir())) >= 100: raise ValueError("Límite de paquetes locales alcanzado.")
        temporary = safe_under(self.root, ".local", "tradingview-bundles", "preparing-" + uuid4().hex)
        write_bundle(temporary, contract)
        # Ambos directorios absolutos han sido comprobados dentro del mismo
        # almacén. Nunca se mueve o elimina una ruta aportada por un cliente.
        try: temporary.rename(target)
        except FileExistsError:
            if self.get(identity)["contract"] != contract: raise ValueError("Conflicto al publicar el paquete local.")
        return {"id": identity, "created": True}

    def get(self, identity):
        identity = hash_id(identity)
        directory = safe_under(self.root, ".local", "tradingview-bundles", identity)
        for name in ("manifest.json", "contract.json", "strategy.pine", "alert-message.json.txt"):
            path = safe_under(self.root, ".local", "tradingview-bundles", identity, name)
            if not path.is_file() or path.stat().st_size > 65536: raise KeyError("Paquete incompleto o excesivo.")
        contract = verify_bundle(directory)
        if checksum(contract) != identity: raise ValueError("El directorio no corresponde al contrato.")
        return {"id": identity, "contract": contract, "pine": (directory / "strategy.pine").read_text(encoding="utf-8"),
                "alert_message": (directory / "alert-message.json.txt").read_text(encoding="utf-8"),
                "manifest": strict_json((directory / "manifest.json").read_bytes())}

    def overview(self):
        parent = safe_under(self.root, ".local", "tradingview-bundles")
        if not parent.exists(): return {"bundles": [], "warnings": []}
        bundles, warnings = [], []
        for path in sorted(parent.iterdir()):
            if path.name.startswith("preparing-"):
                warnings.append("Hay una preparación incompleta conservada para revisión."); continue
            try:
                item = self.get(path.name)
                bundles.append({"id": item["id"], "market": item["contract"]["market"], "strategy": item["contract"]["strategy"],
                                "account": item["contract"]["account"], "pine_compiled": False, "chart_verified": False})
            except (OSError, ValueError, TypeError, KeyError) as error: warnings.append(path.name + ": " + str(error))
            if len(bundles) + len(warnings) >= 100: break
        return {"bundles": bundles, "warnings": warnings}


def validate_mapping(mapping):
    fields(mapping, ("protocol", "columns", "delimiter", "decimal_separator", "grouping_separator", "sides", "time_format", "sequence_mode", "source_is_simulated"), "mapa CSV")
    if mapping["protocol"] != "tiresias_execution_csv_mapping_v1" or mapping["source_is_simulated"] is not True: raise ValueError("Mapa de ejecuciones simuladas requerido.")
    fields(mapping["columns"], COLUMNS, "columnas CSV")
    names = list(mapping["columns"].values())
    if any(value is None and key != "fee" or value is not None and (not isinstance(value, str) or not 1 <= len(value) <= 80) for key, value in mapping["columns"].items()): raise ValueError("Todas las columnas son obligatorias salvo costes desconocidos.")
    if len([name for name in names if name is not None]) != len(set(name for name in names if name is not None)): raise ValueError("No se reutiliza una columna para significados diferentes.")
    if mapping["delimiter"] not in (",", ";", "\t") or mapping["decimal_separator"] not in (".", ","): raise ValueError("Separadores no admitidos.")
    if mapping["grouping_separator"] not in (None, ".", ",", " ") or mapping["grouping_separator"] == mapping["decimal_separator"]: raise ValueError("Separador de miles ambiguo.")
    if not isinstance(mapping["sides"], dict) or not 1 <= len(mapping["sides"]) <= 20 or any(not isinstance(key, str) or not 1 <= len(key) <= 50 or value not in ("buy", "sell") for key, value in mapping["sides"].items()): raise ValueError("Acciones CSV no declaradas.")
    if mapping["time_format"] not in ("iso8601", "unix_ms", "utc_ymd_hm", "utc_dmy_hm") or mapping["sequence_mode"] not in ("column", "trade_number"): raise ValueError("Formato temporal o secuencia no declarado.")
    return mapping


def parse_numeric(text, mapping):
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 64: raise ValueError("Número CSV ausente o excesivo.")
    value = text.strip()
    group, decimal = mapping["grouping_separator"], mapping["decimal_separator"]
    if group and group in value:
        if decimal in value and group in value.split(decimal, 1)[1]: raise ValueError("Separador de miles dentro de la fracción.")
        integer = value.split(decimal)[0]
        if not re.fullmatch(r"[+-]?\d{1,3}(?:" + re.escape(group) + r"\d{3})+", integer): raise ValueError("Agrupación de miles incompatible con el mapa.")
        value = value.replace(group, "")
    if value.count(decimal) > 1: raise ValueError("Separador decimal repetido.")
    value = value.replace(decimal, ".")
    if not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", value): raise ValueError("Número no reconocido; no se eliminan monedas o signos arbitrarios.")
    number(value, "valor CSV")
    return value


def parse_time(text, mode):
    if not isinstance(text, str) or len(text) > 40: raise ValueError("Fecha CSV requerida.")
    text = text.strip()
    if mode == "iso8601": return instant(text)
    if mode == "unix_ms":
        if not re.fullmatch(r"\d{1,13}", text): raise ValueError("Milisegundos Unix inválidos.")
        return instant((datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=int(text))).isoformat())
    pattern = "%Y-%m-%d %H:%M" if mode == "utc_ymd_hm" else "%d/%m/%Y %H:%M"
    return instant(datetime.strptime(text, pattern).replace(tzinfo=UTC).isoformat())


def preview_csv(raw, mapping, contract):
    mapping, contract = validate_mapping(mapping), validate_contract(contract)
    if not isinstance(raw, bytes) or not 1 <= len(raw) <= 2 * 1024 * 1024: raise ValueError("CSV entre 1 byte y 2 MiB requerido.")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""), delimiter=mapping["delimiter"], strict=True)
    headers = reader.fieldnames
    if headers is None or len(headers) != len(set(headers)) or any(name not in headers for name in mapping["columns"].values() if name is not None): raise ValueError("Columnas ausentes o duplicadas; requiere mapa del archivo real.")
    rows, errors, identities, sequences = [], [], set(), set()
    for line, record in enumerate(reader, 2):
        if line > 1001: raise ValueError("La importación está limitada a 1000 filas por archivo.")
        try:
            if None in record or any(value is None for value in record.values()): raise ValueError("Fila CSV desalineada.")
            values = {key: None if name is None else record[name].strip() for key, name in mapping["columns"].items()}
            if values["side"] not in mapping["sides"]: raise ValueError("Tipo de operación no declarado en el mapa.")
            side = mapping["sides"][values["side"]]
            if not re.fullmatch(r"[1-9]\d{0,5}", values["sequence"]): raise ValueError("Secuencia o número de operación inválido.")
            sequence = int(values["sequence"])
            if mapping["sequence_mode"] == "trade_number": sequence = sequence * 2 - (1 if side == "buy" else 0)
            event = {"protocol": "tiresias_simulated_fill_v1", "contract_sha256": checksum(contract),
                     "execution_id": values["execution_id"], "sequence": sequence, "side": side,
                     **{key: None if values[key] is None else parse_numeric(values[key], mapping) for key in ("quantity", "price", "fee")},
                     **{key: parse_time(values[key], mapping["time_format"]) for key in ("signal_at", "executed_at")}, "currency": contract["account"]["currency"]}
            event = validate_fill(event, contract)
            if event["execution_id"] in identities: raise ValueError("Identidad duplicada dentro del archivo.")
            if event["sequence"] in sequences: raise ValueError("Secuencia duplicada dentro del archivo.")
            identities.add(event["execution_id"])
            sequences.add(event["sequence"])
            rows.append({"line": line, "event": event})
        except (ValueError, TypeError, OverflowError) as error: errors.append({"line": line, "reason": str(error)})
    if not rows and not errors: errors.append({"line": 1, "reason": "Archivo sin ejecuciones."})
    return {"protocol": "tiresias_mapped_csv_preview_v1", "raw_sha256": sha256(raw).hexdigest(), "mapping_sha256": checksum(mapping),
            "contract_sha256": checksum(contract), "rows": rows, "errors": errors, "external_format_verified": False,
            "notice": "Normalización según mapa explícito; no acredita un formato TradingView real ni ejecuciones de bróker."}


@contextmanager
def import_lock(root):
    path = safe_under(Path(root).resolve(), ".local", "tradingview-imports", ".writer.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a+b")
    try:
        if path.stat().st_size == 0: stream.write(b"0"); stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error: raise ValueError("Hay otra importación activa; no se abre un segundo escritor.") from error
        yield
    finally: stream.close()


def import_csv(root, ledger, raw, mapping, contract, *, approved_preview_sha256):
    preview = preview_csv(raw, mapping, contract)
    if approved_preview_sha256 != checksum(preview): raise ValueError("La vista previa cambió; revisar antes de importar.")
    if preview["errors"]: raise ValueError("Hay filas inválidas; ninguna fila se importa.")
    with import_lock(root): return _store_import(root, ledger, raw, mapping, preview)


def _store_import(root, ledger, raw, mapping, preview):
    identity = checksum({"raw": preview["raw_sha256"], "mapping": preview["mapping_sha256"], "contract": preview["contract_sha256"]})
    directory = safe_under(Path(root).resolve(), ".local", "tradingview-imports", identity)
    if not directory.exists():
        if sum(path.is_dir() for path in directory.parent.iterdir()) >= 100: raise ValueError("Límite de cien importaciones locales.")
        directory.mkdir(parents=True, exist_ok=False)
        (directory / "original.csv").write_bytes(raw)
        (directory / "mapping.json").write_bytes(canonical(mapping))
        (directory / "preview.json").write_bytes(canonical(preview))
        (directory / "progress.jsonl").touch(exist_ok=False)
    for name, expected in (("original.csv", raw), ("mapping.json", canonical(mapping)), ("preview.json", canonical(preview))):
        path = safe_under(Path(root).resolve(), ".local", "tradingview-imports", identity, name)
        if path.read_bytes() != expected: raise ValueError("El original, mapa o vista previa archivados cambiaron.")
    progress = safe_under(Path(root).resolve(), ".local", "tradingview-imports", identity, "progress.jsonl")
    done = {}
    expected_rows = {row["line"]: row for row in preview["rows"]}
    for line in progress.read_bytes().splitlines():
        record = strict_json(line)
        if record.get("line") not in expected_rows or record.get("event_sha256") != checksum(expected_rows[record["line"]]["event"]): raise ValueError("Progreso de importación alterado.")
        receipt = ledger.receipt(record["receipt"])
        if receipt["raw"] != canonical(expected_rows[record["line"]]["event"]).decode(): raise ValueError("Recepción de importación incompatible.")
        done[record["line"]] = record
    for row in preview["rows"]:
        if row["line"] in done: continue
        result = ledger.receive(canonical(row["event"]), transport="file_import", source={"import_id": identity, "csv_line": row["line"], "raw_sha256": preview["raw_sha256"], "mapping_sha256": preview["mapping_sha256"]})
        record = {"line": row["line"], "event_sha256": checksum(row["event"]), **result}
        with progress.open("ab") as stream:
            stream.write(canonical(record) + b"\n"); stream.flush(); os.fsync(stream.fileno())
        done[row["line"]] = record
    result = {"id": identity, "status": "stored_in_inbox_not_processed", "rows": len(done), "receipts": list(done.values()),
              "source_sha256": preview["raw_sha256"], "external_format_verified": False}
    completed = safe_under(Path(root).resolve(), ".local", "tradingview-imports", identity, "completion.json")
    if completed.exists():
        if strict_json(completed.read_bytes()) != result: raise ValueError("Finalización de importación alterada.")
    else: completed.write_bytes(canonical(result))
    return result
