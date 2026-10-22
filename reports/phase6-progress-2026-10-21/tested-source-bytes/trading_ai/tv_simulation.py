"""Inbox duradero y contabilidad virtual. Recibir un evento no lo contabiliza."""

from contextlib import contextmanager
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from pathlib import Path
import sqlite3
from uuid import uuid4

from trading_ai.tv_contracts import (canonical, checksum, decimal_text, fields, hash_id, instant,
                                     number, safe_under, strict_json, validate_contract, validate_fill)


RISK = {"max_drawdown_fraction": "0.2", "max_orders": 1000, "max_price_age_seconds": 172800,
        "fee_tolerance": "0.01"}


def now(): return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def engine_hashes():
    return {name: sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ("tv_simulation.py", "tv_contracts.py")}


def normalize_pine(value, contract):
    fields(value, ("protocol", "contract_sha256", "ticker", "timeframe", "side", "quantity", "price", "executed_at", "execution_time_basis", "alert_fired_at", "currency", "order_meta"), "alerta Pine")
    if value["protocol"] != "tiresias_pine_fill_v1" or value["ticker"] != contract["market"]["ticker"] or value["timeframe"] != "1D": raise ValueError("Alerta de símbolo o formato incompatible.")
    if value["execution_time_basis"] != "bar_open_by_contract" or instant(value["alert_fired_at"]) < instant(value["executed_at"]): raise ValueError("Reloj de alerta incompatible con la apertura declarada.")
    meta = value["order_meta"]
    fields(meta, ("sequence", "execution_id", "signal_time_ms"), "metadatos Pine")
    ms = meta["signal_time_ms"]
    if type(ms) is not int or not 0 <= ms <= 4102444800000: raise ValueError("Instante de señal Pine inválido.")
    signal = (datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=ms)).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    result = {"protocol": "tiresias_simulated_fill_v1", "contract_sha256": value["contract_sha256"],
              "execution_id": meta["execution_id"], "sequence": meta["sequence"], "side": value["side"],
              "quantity": value["quantity"], "price": value["price"], "fee": None, "currency": value["currency"],
              "signal_at": signal, "executed_at": value["executed_at"]}
    return validate_fill(result, contract)


class SimulationLedger:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.path = safe_under(self.root, ".local", "simulation", "ledger.sqlite3")

    @contextmanager
    def connection(self, write=False):
        safe_under(self.root, ".local", "simulation", "ledger.sqlite3")
        if write: self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = None
        try:
            conn = sqlite3.connect(str(self.path) if write else self.path.as_uri() + "?mode=ro", uri=not write, timeout=1)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys=ON")
            if write:
                conn.execute("PRAGMA synchronous=FULL")
                conn.execute("BEGIN IMMEDIATE")
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    if conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone(): raise ValueError("Registro desconocido; no se reinicia.")
                    for sql in (
                        "CREATE TABLE contracts (id TEXT PRIMARY KEY, data TEXT NOT NULL, risk TEXT NOT NULL, risk_hash TEXT NOT NULL, engine TEXT NOT NULL, created TEXT NOT NULL)",
                        "CREATE TABLE receipts (id TEXT PRIMARY KEY, raw BLOB NOT NULL, hash TEXT NOT NULL, transport TEXT NOT NULL, source TEXT NOT NULL, received TEXT NOT NULL, state TEXT NOT NULL, reason TEXT, account TEXT, execution TEXT)",
                        "CREATE TABLE events (account TEXT REFERENCES contracts(id), execution TEXT NOT NULL, sequence INTEGER NOT NULL, data TEXT NOT NULL, hash TEXT NOT NULL, receipt TEXT REFERENCES receipts(id), state TEXT NOT NULL, reason TEXT, PRIMARY KEY(account,execution), UNIQUE(account,sequence))",
                        "CREATE TABLE postings (id INTEGER PRIMARY KEY, account TEXT REFERENCES contracts(id), data TEXT NOT NULL, previous TEXT NOT NULL, hash TEXT NOT NULL)",
                    ): conn.execute(sql)
                    conn.execute("PRAGMA user_version=1")
                elif version != 1: raise ValueError("Versión del simulador desconocida; no se reinicia.")
            else:
                conn.execute("PRAGMA query_only=ON")
                conn.execute("BEGIN")  # Estado, pendientes y huella de revisión comparten una instantánea.
                if conn.execute("PRAGMA user_version").fetchone()[0] != 1: raise ValueError("Registro incompatible.")
            yield conn
            if write: conn.commit()
        except sqlite3.Error as error:
            raise ValueError("No se pudo comprobar el registro de simulación: " + str(error)) from error
        finally:
            if conn is not None: conn.close()

    def register(self, contract, risk=None):
        c, risk = validate_contract(contract), deepcopy(RISK if risk is None else risk)
        fields(risk, RISK, "límites de riesgo")
        number(risk["max_drawdown_fraction"], "drawdown límite", maximum=Decimal(1), positive=True)
        number(risk["fee_tolerance"], "tolerancia de coste", maximum=Decimal(1))
        for key in ("max_drawdown_fraction", "fee_tolerance"): risk[key] = decimal_text(Decimal(risk[key]))
        if type(risk["max_orders"]) is not int or not 1 <= risk["max_orders"] <= 10000: raise ValueError("Límite de operaciones inválido.")
        if type(risk["max_price_age_seconds"]) is not int or not 1 <= risk["max_price_age_seconds"] <= 604800: raise ValueError("Antigüedad máxima inválida.")
        account = checksum(c)
        with self.connection(True) as conn:
            row = conn.execute("SELECT * FROM contracts WHERE id=?", (account,)).fetchone()
            if row:
                if row["data"] != canonical(c).decode() or row["risk"] != canonical(risk).decode(): raise ValueError("La cuenta existe con otros límites; no se sobrescribe.")
                return {"account": account, "created": False}
            if conn.execute("SELECT count(*) FROM contracts").fetchone()[0] >= 100: raise ValueError("Límite de cien cuentas virtuales.")
            conn.execute("INSERT INTO contracts VALUES (?,?,?,?,?,?)", (account, canonical(c).decode(), canonical(risk).decode(), checksum(risk), canonical(engine_hashes()).decode(), now()))
        return {"account": account, "created": True}

    def _contract(self, conn, account, *, action=False):
        hash_id(account)
        row = conn.execute("SELECT * FROM contracts WHERE id=?", (account,)).fetchone()
        if row is None: raise KeyError("Cuenta o contrato no registrado.")
        c, risk = validate_contract(strict_json(row["data"])), strict_json(row["risk"])
        if checksum(c) != account or checksum(risk) != row["risk_hash"]: raise ValueError("Contrato o riesgo alterados.")
        if action and strict_json(row["engine"]) != engine_hashes(): raise ValueError("El motor cambió desde el registro; se requiere una cuenta revisada, sin reiniciar esta.")
        return c, risk

    def receive(self, raw, *, transport="file_import", source=None):
        if not isinstance(raw, bytes) or not 1 <= len(raw) <= 65536: raise ValueError("Evento entre 1 y 65536 bytes requerido.")
        if transport not in ("file_import", "authenticated_webhook", "manual_simulation"): raise ValueError("Transporte no admitido.")
        source = {} if source is None else source
        if not isinstance(source, dict) or len(canonical(source)) > 4096: raise ValueError("Procedencia excesiva.")
        receipt, account, execution, state, reason = uuid4().hex, None, None, "invalid", None
        with self.connection(True) as conn:
            counts = conn.execute("SELECT count(*),coalesce(sum(length(raw)),0) FROM receipts").fetchone()
            if counts[0] >= 10000 or counts[1] + len(raw) > 64 * 1024 * 1024: raise ValueError("Inbox lleno; no se confirma una recepción que no puede conservarse.")
            conn.execute("INSERT INTO receipts VALUES (?,?,?,?,?,?,?,?,?,?)", (receipt, raw, sha256(raw).hexdigest(), transport, canonical(source).decode(), now(), state, None, None, None))
            try:
                value = strict_json(raw)
                if not isinstance(value, dict): raise ValueError("Evento JSON objeto requerido.")
                account = hash_id(value.get("contract_sha256"))
                contract, _ = self._contract(conn, account)
                event = normalize_pine(value, contract) if value.get("protocol") == "tiresias_pine_fill_v1" else validate_fill(value, contract)
                execution, event_hash = event["execution_id"], checksum(event)
                previous = conn.execute("SELECT * FROM events WHERE account=? AND (execution=? OR sequence=?)", (account, execution, event["sequence"])).fetchall()
                if previous:
                    state = "duplicate" if len(previous) == 1 and previous[0]["hash"] == event_hash else "conflict"
                    reason = None if state == "duplicate" else "Identidad o secuencia reutilizada con contenido diferente."
                else:
                    conn.execute("INSERT INTO events VALUES (?,?,?,?,?,?,'pending',NULL)", (account, execution, event["sequence"], canonical(event).decode(), event_hash, receipt))
                    state = "queued"
            except KeyError as error: state, reason = "unknown_contract", str(error)
            except (ValueError, TypeError, UnicodeError, OverflowError, RecursionError) as error: state, reason = "invalid", str(error)[:500]
            conn.execute("UPDATE receipts SET state=?,reason=?,account=?,execution=? WHERE id=?", (state, reason, account, execution, receipt))
        return {"receipt": receipt, "state": state, "reason": reason, "account": account, "execution": execution}

    def _initial(self, c):
        return {"cash": c["account"]["initial_capital"], "quantity": "0", "basis": "0", "realized_pnl": "0", "fees": "0",
                "equity": c["account"]["initial_capital"], "peak": c["account"]["initial_capital"], "max_drawdown_percent": "0",
                "last_sequence": 0, "last_at": None, "price": None, "price_at": None, "filled_orders": 0,
                "rejections": 0, "estimated_fee_events": 0, "risk_paused": False, "last_reason": None}

    def _state(self, conn, account, c):
        state, previous = self._initial(c), "0" * 64
        for row in conn.execute("SELECT * FROM postings WHERE account=? ORDER BY id", (account,)):
            record = strict_json(row["data"])
            if row["previous"] != previous or checksum({"account": account, "previous": previous, "record": record}) != row["hash"]:
                raise ValueError("Cadena contable alterada; no se reconstruye silenciosamente.")
            state, previous = record["state"], row["hash"]
        observed = conn.execute("SELECT coalesce(max(sequence),0) FROM events WHERE account=? AND state IN ('applied','rejected')", (account,)).fetchone()[0]
        if state["last_sequence"] != observed: raise ValueError("El estado y la secuencia contabilizada no coinciden.")
        return state, previous

    def _post(self, conn, account, record, previous):
        if conn.execute("SELECT count(*) FROM postings WHERE account=?", (account,)).fetchone()[0] >= 10000: raise ValueError("Límite de asientos de la cuenta alcanzado.")
        hashed = checksum({"account": account, "previous": previous, "record": record})
        conn.execute("INSERT INTO postings (account,data,previous,hash) VALUES (?,?,?,?)", (account, canonical(record).decode(), previous, hashed))
        return hashed

    def _apply(self, event, state, c, risk):
        result, reason = deepcopy(state), None
        with localcontext(Context(prec=28)):
            cash, held, basis = [Decimal(state[key]) for key in ("cash", "quantity", "basis")]
            quantity, price = Decimal(event["quantity"]), Decimal(event["price"])
            expected_fee = quantity * price * Decimal(c["account"]["cost_rate"])
            fee = expected_fee if event["fee"] is None else Decimal(event["fee"])
            if state["last_at"] and event["executed_at"] < state["last_at"]: reason = "out_of_order_execution"
            elif quantity > Decimal(c["account"]["quantity"]): reason = "quantity_limit"
            elif abs(fee - expected_fee) > Decimal(risk["fee_tolerance"]): reason = "fee_discrepancy"
            elif state["filled_orders"] >= risk["max_orders"] and event["side"] == "buy": reason = "order_limit"
            elif event["side"] == "buy" and state["risk_paused"]: reason = "risk_paused"
            elif event["side"] == "buy" and held > 0: reason = "pyramiding_not_allowed"
            elif event["side"] == "buy" and quantity * price + fee > cash: reason = "insufficient_cash"
            elif event["side"] == "sell" and quantity > held: reason = "insufficient_position"
            elif event["side"] == "sell" and cash + quantity * price - fee < 0: reason = "insufficient_cash_for_fee"
            result["last_sequence"] = event["sequence"]
            result["last_reason"] = reason
            if reason:
                result["rejections"] += 1
                result["last_at"] = max(state["last_at"] or event["executed_at"], event["executed_at"])
                result["risk_paused"] = True
                return result, reason
            if event["side"] == "buy":
                cash -= quantity * price + fee; basis = quantity * price + fee; held = quantity
            else:
                portion = basis * quantity / held
                cash += quantity * price - fee; basis -= portion; held -= quantity
                result["realized_pnl"] = decimal_text(Decimal(result["realized_pnl"]) + quantity * price - fee - portion)
            result.update(cash=decimal_text(cash), quantity=decimal_text(held), basis=decimal_text(basis),
                          fees=decimal_text(Decimal(result["fees"]) + fee), last_at=event["executed_at"],
                          price=event["price"], price_at=event["executed_at"], filled_orders=result["filled_orders"] + 1,
                          estimated_fee_events=result["estimated_fee_events"] + (event["fee"] is None))
            self._value(result, risk)
        return result, None

    @staticmethod
    def _value(state, risk):
        equity = Decimal(state["cash"]) + Decimal(state["quantity"]) * Decimal(state["price"])
        peak = max(Decimal(state["peak"]), equity)
        dd = (peak - equity) / peak * 100
        state.update(equity=decimal_text(equity), peak=decimal_text(peak),
                     max_drawdown_percent=decimal_text(max(Decimal(state["max_drawdown_percent"]), dd)),
                     risk_paused=state["risk_paused"] or dd >= Decimal(risk["max_drawdown_fraction"]) * 100)

    @staticmethod
    def _review(conn, account, chain):
        pending = [dict(row) for row in conn.execute("SELECT sequence,hash FROM events WHERE account=? AND state='pending' ORDER BY sequence", (account,))]
        problems = [dict(row) for row in conn.execute("SELECT id,hash,state FROM receipts WHERE account=? AND state IN ('invalid','conflict','unknown_contract') ORDER BY rowid", (account,))]
        return checksum({"chain": chain, "pending": pending, "problem_receipts": problems})

    def process(self, account, *, limit=1000, expected_chain=None, expected_review=None):
        if type(limit) is not int or not 1 <= limit <= 1000: raise ValueError("Lote inválido.")
        applied, rejected = [], []
        with self.connection(True) as conn:
            c, risk = self._contract(conn, account, action=True)
            state, chain = self._state(conn, account, c)
            if expected_chain is not None and expected_chain != chain: raise ValueError("La cuenta cambió desde la revisión; recarga antes de procesar.")
            if expected_review is not None and expected_review != self._review(conn, account, chain): raise ValueError("El inbox cambió desde la revisión; recarga antes de procesar.")
            for _ in range(limit):
                row = conn.execute("SELECT * FROM events WHERE account=? AND sequence=? AND state='pending'", (account, state["last_sequence"] + 1)).fetchone()
                if row is None: break
                event = validate_fill(strict_json(row["data"]), c)
                if checksum(event) != row["hash"]: raise ValueError("Evento normalizado alterado.")
                state, reason = self._apply(event, state, c, risk)
                chain = self._post(conn, account, {"kind": "fill", "execution": event["execution_id"], "event_sha256": row["hash"], "state": state}, chain)
                conn.execute("UPDATE events SET state=?,reason=? WHERE account=? AND execution=?", ("rejected" if reason else "applied", reason, account, event["execution_id"]))
                (rejected if reason else applied).append(event["execution_id"])
        return {"account": account, "applied": applied, "rejected": rejected, "next_sequence": state["last_sequence"] + 1}

    def mark(self, account, *, price, at, mark_id, expected_chain=None):
        if not isinstance(mark_id, str) or not 1 <= len(mark_id) <= 128: raise ValueError("Identificador de valoración requerido.")
        price, at = decimal_text(number(price, "precio", positive=True)), instant(at)
        with self.connection(True) as conn:
            c, risk = self._contract(conn, account, action=True)
            state, chain = self._state(conn, account, c)
            for row in conn.execute("SELECT data FROM postings WHERE account=?", (account,)):
                old = strict_json(row[0])
                if old.get("mark_id") == mark_id:
                    if old["state"]["price"] != price or old["state"]["price_at"] != at: raise ValueError("Valoración repetida con otros datos.")
                    return {"mark_id": mark_id, "duplicate": True}
            if expected_chain is not None and expected_chain != chain: raise ValueError("La cuenta cambió desde la revisión; recarga antes de valorar.")
            if state["last_at"] and at < state["last_at"]: raise ValueError("Valoración atrasada; no modifica el historial.")
            with localcontext(Context(prec=28)):
                state.update(price=price, price_at=at, last_at=at)
                self._value(state, risk)
            self._post(conn, account, {"kind": "mark", "mark_id": mark_id, "state": state}, chain)
        return {"mark_id": mark_id, "duplicate": False}

    def account(self, account, *, as_of=None):
        with self.connection() as conn:
            c, risk = self._contract(conn, account)
            engine_compatible = strict_json(conn.execute("SELECT engine FROM contracts WHERE id=?", (account,)).fetchone()[0]) == engine_hashes()
            state, chain = self._state(conn, account, c)
            events = [dict(row) for row in conn.execute("SELECT execution,sequence,state,reason FROM events WHERE account=? ORDER BY sequence", (account,))]
            pending = [row for row in events if row["state"] == "pending"]
            pending_events = []
            for row in conn.execute("SELECT data,hash FROM events WHERE account=? AND state='pending' ORDER BY sequence LIMIT 100", (account,)):
                event = validate_fill(strict_json(row["data"]), c)
                if checksum(event) != row["hash"]: raise ValueError("Evento pendiente alterado.")
                pending_events.append(event)
            review = self._review(conn, account, chain)
            problems = [dict(row) for row in conn.execute("SELECT id,hash,state,reason,execution FROM receipts WHERE account=? AND state IN ('invalid','conflict','unknown_contract') ORDER BY rowid DESC", (account,))]
        query_time = instant(now() if as_of is None else as_of)
        age = None if state["price_at"] is None else (datetime.fromisoformat(query_time.replace("Z", "+00:00")) - datetime.fromisoformat(state["price_at"].replace("Z", "+00:00"))).total_seconds()
        return {"account": account, "contract": c, "risk": risk, "state": state, "chain_sha256": chain,
                "engine_compatible": engine_compatible,
                "events": events, "pending_events": pending_events, "pending_count": len(pending), "review_sha256": review,
                "problem_receipts": problems[:200], "problem_count": len(problems),
                "waiting_for_sequence": state["last_sequence"] + 1 if pending else None,
                "queried_at": query_time, "price_age_seconds": age, "price_stale": age is None or age < 0 or age > risk["max_price_age_seconds"],
                "source_notice": "Simulación con eventos aportados; no es saldo de bróker ni cotización actual verificada."}

    def overview(self):
        if not self.path.exists(): return {"accounts": [], "receipts": []}
        with self.connection() as conn:
            accounts = [dict(row) for row in conn.execute("SELECT id,created FROM contracts ORDER BY created DESC")]
            receipts = [dict(row) for row in conn.execute("SELECT id,hash,transport,received,state,reason,account,execution FROM receipts ORDER BY rowid DESC LIMIT 200")]
        return {"accounts": accounts, "receipts": receipts}

    def receipt(self, receipt):
        if not isinstance(receipt, str) or len(receipt) != 32 or any(ch not in "0123456789abcdef" for ch in receipt): raise ValueError("Identificador de recepción inválido.")
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM receipts WHERE id=?", (receipt,)).fetchone()
            if row is None: raise KeyError(receipt)
            result = dict(row)
            if sha256(result["raw"]).hexdigest() != result["hash"]: raise ValueError("Original del evento alterado.")
            result["raw"] = result["raw"].decode("utf-8", errors="replace")
            result["source"] = strict_json(result["source"])
            return result

    def reconcile(self, account, external, *, tolerance="0.01"):
        fields(external, ("as_of", "currency", "cash", "quantity", "equity"), "estado externo")
        current = self.account(account, as_of=external["as_of"])
        if external["currency"] != current["contract"]["account"]["currency"]: raise ValueError("No se comparan monedas diferentes.")
        tolerance = number(tolerance, "tolerancia", maximum=Decimal(1))
        with localcontext(Context(prec=28)):
            differences = {}
            for key in ("cash", "quantity", "equity"):
                value = external[key]
                differences[key] = None if value is None else decimal_text(Decimal(current["state"][key]) - number(value, key, minimum=Decimal("-1e12")))
        comparable = current["state"]["last_at"] == instant(external["as_of"])
        return {"account": account, "comparable_at_same_time": comparable, "differences_local_minus_external": differences,
                "matches": comparable and all(value is not None and Decimal(value).copy_abs() <= tolerance for value in differences.values()),
                "local_capital_replaced": False}
