"""Acciones locales explícitas de la interfaz de simulación, sin autoridad del LLM."""

import base64
import binascii
import csv
import threading

from trading_ai.data import SUPPORTED_PAIRS
from trading_ai.dukascopy_service import DukascopyResearch
from trading_ai.execution_comparison import ExecutionComparisons, POLICY, declaration_template, mapping_template
from trading_ai.jforex_reconciliation import JForexReconciliations
from trading_ai.tv_contracts import checksum, fields, hash_id, make_contract
from trading_ai.tv_io import COLUMNS
from trading_ai.tv_io import BundleRepository, import_csv, preview_csv
from trading_ai.tv_simulation import RISK, SimulationLedger


class SimulationService:
    def __init__(self, root):
        self.root = root
        self.ledger, self.bundles = SimulationLedger(root), BundleRepository(root)
        self.dukascopy = DukascopyResearch(root)
        self.executions = ExecutionComparisons(root)
        self.jforex = JForexReconciliations(root)
        self._writer = threading.Lock()

    def overview(self):
        return {**self.ledger.overview(), **self.bundles.overview(), "risk_defaults": dict(RISK), "contract_template": make_contract(),
                "mapping_template": {"protocol": "tiresias_execution_csv_mapping_v1", "columns": {key: key for key in COLUMNS},
                                     "delimiter": ",", "decimal_separator": ".", "grouping_separator": None,
                                     "sides": {"buy": "buy", "sell": "sell"}, "time_format": "iso8601", "sequence_mode": "column", "source_is_simulated": True},
                "supported_pairs": list(SUPPORTED_PAIRS), "external_connection": False, "dukascopy": self.dukascopy.overview(),
                "execution_comparisons": self.executions.overview(), "execution_mapping_template": mapping_template(),
                "execution_policy_template": dict(POLICY), "execution_declaration_template": declaration_template(),
                "jforex_reconciliations": self.jforex.overview(),
                "notice": "FASE 6 en desarrollo: paquetes Pine sin compilación externa, cuentas virtuales y recepción local de eventos aportados."}

    def get(self, resource, identity):
        if resource == "accounts": return self.ledger.account(identity)
        if resource == "bundles": return self.bundles.get(identity)
        if resource == "receipts": return self.ledger.receipt(identity)
        if resource == "dukascopy": return self.dukascopy.get(identity)
        if resource == "price-histories": return self.dukascopy.dataset(identity)
        if resource == "market-comparisons": return self.dukascopy.comparison(identity)
        if resource == "market-benchmarks": return self.dukascopy.benchmark_result(identity)
        if resource == "execution-comparisons": return self.executions.get(identity)
        if resource == "jforex-reconciliations": return self.jforex.get(identity)
        raise KeyError(resource)

    @staticmethod
    def _csv(body):
        raw = body["csv_base64"]
        if not isinstance(raw, str) or not 1 <= len(raw) <= 2800000: raise ValueError("CSV codificado ausente o excesivo.")
        try: return base64.b64decode(raw, validate=True)
        except (ValueError, binascii.Error) as error: raise ValueError("CSV codificado inválido.") from error

    def action(self, body):
        if not self._writer.acquire(blocking=False): raise ValueError("Hay otra acción de simulación activa; espera antes de volver a intentarlo.")
        try: return self._action(body)
        except csv.Error as error: raise ValueError("CSV mal formado: " + str(error)) from error
        finally: self._writer.release()

    def _action(self, body):
        if not isinstance(body, dict): raise ValueError("Acción JSON requerida.")
        action = body.get("action")
        if action in ("preview_jforex_reconciliation", "save_jforex_reconciliation"):
            expected = ("action", "run", "name", "zip_base64", "html_timezone")
            if action == "save_jforex_reconciliation": expected += ("approve_preview_sha256",)
            fields(body, expected, "conciliación JForex")
            values = {key:body[key] for key in ("run","name","html_timezone")}
            values["raw"] = self._csv({"csv_base64":body["zip_base64"]})
            if action == "preview_jforex_reconciliation": return self.jforex.preview(**values)
            return self.jforex.save(approval_sha256=body["approve_preview_sha256"], **values)
        if action in ("preview_execution_comparison", "save_execution_comparison"):
            expected = ("action", "run", "name", "csv_base64", "mapping", "tolerances", "metadata")
            if action == "save_execution_comparison": expected += ("approve_preview_sha256",)
            fields(body, expected, "contraste de ejecuciones")
            values = {key: body[key] for key in ("run", "name", "mapping", "tolerances", "metadata")}
            values["raw"] = self._csv(body)
            if action == "preview_execution_comparison": return self.executions.preview(**values)
            return self.executions.save(approval_sha256=body["approve_preview_sha256"], **values)
        if action == "benchmark_price_history":
            fields(body, ("action", "dataset", "capital", "quantity"), "referencias y costes")
            return self.dukascopy.benchmark(dataset=body["dataset"], capital=body["capital"], quantity=body["quantity"])
        if action == "compare_price_periods":
            fields(body, ("action", "left", "right"), "comparación de períodos")
            return self.dukascopy.compare(body["left"], body["right"])
        if action == "import_price_history":
            fields(body, ("action", "format", "year", "start_date", "end_date", "files"), "histórico de precios")
            files = body["files"]
            if not isinstance(files, list) or not 1 <= len(files) <= 24:
                raise ValueError("Se requieren entre 1 y 24 archivos de precios.")
            inputs, total = [], 0
            for item in files:
                fields(item, ("name", "side", "content_base64"), "archivo de precios")
                if not isinstance(item["content_base64"], str) or not 1 <= len(item["content_base64"]) <= 2800000:
                    raise ValueError("Archivo codificado ausente o excesivo.")
                try:
                    raw = base64.b64decode(item["content_base64"], validate=True)
                except (ValueError, binascii.Error) as error:
                    raise ValueError("Archivo codificado inválido.") from error
                total += len(raw)
                if total > 2 * 1024 * 1024:
                    raise ValueError("Máximo 2 MiB de precios por importación de la interfaz.")
                inputs.append({"name": item["name"], "side": item["side"], "body": raw})
            return self.dukascopy.import_prices(inputs=inputs, source_format=body["format"], year=body["year"],
                start_date=body["start_date"], end_date=body["end_date"])
        if action == "simulate_dukascopy":
            fields(body, ("action", "dataset", "capital", "quantity", "commission_rate"), "cálculo Dukascopy")
            return self.dukascopy.run(dataset=body["dataset"], capital=body["capital"],
                                      quantity=body["quantity"], commission_rate=body["commission_rate"])
        if action == "prepare_bundle":
            fields(body, ("action", "contract"), "preparación")
            return self.bundles.create(body["contract"])
        if action == "register":
            fields(body, ("action", "bundle", "risk", "approve_virtual_account"), "cuenta virtual")
            if body["approve_virtual_account"] is not True: raise ValueError("Revisión explícita de cuenta virtual requerida.")
            return self.ledger.register(self.bundles.get(body["bundle"])["contract"], body["risk"])
        if action == "receive":
            fields(body, ("action", "raw", "approve_inbox"), "recepción manual")
            if body["approve_inbox"] is not True or not isinstance(body["raw"], str): raise ValueError("Revisar el evento antes de guardarlo en el inbox.")
            return self.ledger.receive(body["raw"].encode("utf-8"), transport="file_import", source={"entrypoint": "local_ui_explicit"})
        if action == "process":
            fields(body, ("action", "account", "chain_sha256", "review_sha256", "approve_processing"), "procesamiento")
            if body["approve_processing"] is not True: raise ValueError("Procesamiento no aprobado.")
            # Requiere revisión de un estado concreto; una visita GET nunca llama aquí.
            return self.ledger.process(body["account"], limit=100, expected_chain=hash_id(body["chain_sha256"]), expected_review=hash_id(body["review_sha256"]))
        if action == "mark":
            fields(body, ("action", "account", "price", "at", "mark_id", "chain_sha256", "approve_valuation"), "valoración")
            if body["approve_valuation"] is not True: raise ValueError("Valoración no aprobada.")
            return self.ledger.mark(body["account"], price=body["price"], at=body["at"], mark_id=body["mark_id"], expected_chain=hash_id(body["chain_sha256"]))
        if action == "reconcile":
            fields(body, ("action", "account", "external"), "conciliación")
            return self.ledger.reconcile(body["account"], body["external"])
        if action in ("preview_csv", "import_csv"):
            expected = ("action", "bundle", "csv_base64", "mapping") + (("approve_preview_sha256",) if action == "import_csv" else ())
            fields(body, expected, "CSV")
            c, raw = self.bundles.get(body["bundle"])["contract"], self._csv(body)
            if action == "preview_csv":
                preview = preview_csv(raw, body["mapping"], c)
                return {"preview": preview, "approval_sha256": checksum(preview)}
            self.ledger.account(body["bundle"])  # La interfaz no importa a cuentas desconocidas.
            return import_csv(self.root, self.ledger, raw, body["mapping"], c, approved_preview_sha256=body["approve_preview_sha256"])
        raise ValueError("Acción de simulación desconocida.")
