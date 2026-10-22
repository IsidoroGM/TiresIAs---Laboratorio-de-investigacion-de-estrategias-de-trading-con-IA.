"""Consulta y cálculo explícito de históricos locales; nunca descarga desde la web."""

from itertools import islice
from hashlib import sha256
from pathlib import Path
import re
import uuid

from trading_ai.dukascopy_backtest import PROTOCOL, read_bounded, run_backtest
from trading_ai.dukascopy_history import PROFILE
from trading_ai.market_history import PROFILE as SUPPLIED_PROFILE, prepare
from trading_ai.tv_contracts import checksum, hash_id, safe_under, strict_json


def dataset_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value):
        raise ValueError("Identificador de histórico inválido.")
    return value


class DukascopyResearch:
    def __init__(self, root):
        self.root = Path(root).resolve()

    def directory(self, kind):
        return safe_under(self.root, ".local", "dukascopy" if kind == "datasets" else "dukascopy-research")

    def overview(self):
        result = {"datasets": [], "runs": [], "warnings": [], "strategy": "SMA20/60",
                  "required_sessions": 61, "network_requests": 0, "metadata_only": True}
        for kind in ("datasets", "runs"):
            directory = self.directory(kind)
            if not directory.exists():
                continue
            children = list(islice(directory.iterdir(), 201))
            if len(children) > 200:
                result["warnings"].append(f"Catálogo {kind} limitado a 200 entradas.")
            for child in sorted(children[:200], key=lambda path: path.name):
                try:
                    dataset_id(child.name)
                    child = safe_under(directory, child.name)
                    filename = "manifest.json" if kind == "datasets" else "simulation.json"
                    path = safe_under(child, filename)
                    if not child.is_dir() or not path.is_file():
                        continue
                    value = strict_json(read_bounded(path, 256 * 1024 if kind == "datasets" else 8 * 1024 * 1024))
                    if not isinstance(value, dict):
                        raise ValueError("Resumen JSON inválido.")
                    if kind == "datasets":
                        if value.get("profile") not in (PROFILE, SUPPLIED_PROFILE) or value.get("status") != "prepared":
                            continue
                        if value.get("pair") != "EUR/USD" or type(value.get("daily_sessions")) is not int:
                            raise ValueError("Resumen de mercado incompatible.")
                        result[kind].append({"id": child.name, "pair": value["pair"], "first_month": value.get("first_month"),
                            "last_month": value.get("last_month"), "daily_sessions": value["daily_sessions"],
                            "missing_sessions": max(0, 61 - value["daily_sessions"]),
                            "all_final_transports_https": value.get("all_final_transports_https"),
                            "provider": value.get("provider", "Dukascopy"), "start_date": value.get("start_date"),
                            "end_date_exclusive": value.get("end_date_exclusive"),
                            "internal_gap_count": value.get("internal_gap_count"), "coverage_gap_count": value.get("coverage_gap_count"),
                            "originals_verified_now": False})
                    else:
                        if not re.fullmatch(r"[0-9a-f]{32}", child.name):
                            continue  # Las salidas CLI pueden vivir aquí sin ser fichas de la interfaz.
                        self.validate_result(value)
                        result[kind].append({"id": child.name, "status": value["status"], "daily_sessions": value["daily_sessions"],
                                             "missing_sessions": value["missing_sessions"], "summary": value["summary"]})
                except (ValueError, OSError, UnicodeError) as error:
                    result["warnings"].append(child.name + ": " + str(error))
        return result

    @staticmethod
    def validate_result(value):
        if (not isinstance(value, dict) or value.get("protocol") != PROTOCOL
                or hash_id(value.get("result_sha256")) != checksum({key: item for key, item in value.items() if key != "result_sha256"})):
            raise ValueError("El resultado guardado no coincide con su huella.")

    def run(self, *, dataset, capital, quantity, commission_rate):
        source = safe_under(self.directory("datasets"), dataset_id(dataset))
        identity = uuid.uuid4().hex
        output = safe_under(self.directory("runs"), identity)
        result = run_backtest(history=source, output=output, capital=capital, quantity=quantity, commission_rate=commission_rate)
        return {"id": identity, "status": result["status"], "missing_sessions": result["missing_sessions"], "summary": result["summary"]}

    def import_prices(self, *, inputs, source_format, year, start_date, end_date):
        identity = "prices-" + uuid.uuid4().hex
        result = prepare(inputs=inputs, source_format=source_format, year=year, start_date=start_date, end_date=end_date,
                         output=safe_under(self.directory("datasets"), identity))
        return {"id": identity, "provider": result["provider"], "daily_sessions": result["daily_sessions"],
                "internal_gap_count": result["internal_gap_count"], "coverage_gap_count": result["coverage_gap_count"]}

    def dataset(self, identity):
        from trading_ai.dukascopy_backtest import load_history
        directory = safe_under(self.directory("datasets"), dataset_id(identity))
        daily, provenance, raw, _ = load_history(directory)
        return {"id": identity, "manifest": strict_json(raw), "source": provenance,
                "daily_sessions": len(daily["sessions"]), "missing_sessions": max(0, 61 - len(daily["sessions"])),
                "internal_gaps": [{"date": day["date"], "gaps": day["internal_gaps"]} for day in daily["sessions"] if day["internal_gaps"]],
                "coverage_gaps": daily.get("blocking_gaps", []), "accounting_processed": False}

    def get(self, identity):
        if not isinstance(identity, str) or not re.fullmatch(r"[0-9a-f]{32}", identity):
            raise ValueError("Identificador de cálculo inválido.")
        directory = safe_under(self.directory("runs"), identity)
        result = strict_json(read_bounded(safe_under(directory, "simulation.json"), 8 * 1024 * 1024))
        self.validate_result(result)
        for filename, key, maximum in (("input-manifest.json", "manifest_sha256", 256 * 1024),
                                        ("input-daily.json", "daily_file_sha256", 8 * 1024 * 1024)):
            if sha256(read_bounded(safe_under(directory, filename), maximum)).hexdigest() != result["source"][key]:
                raise ValueError("La copia de entrada no coincide con la del cálculo guardado.")
        return result
