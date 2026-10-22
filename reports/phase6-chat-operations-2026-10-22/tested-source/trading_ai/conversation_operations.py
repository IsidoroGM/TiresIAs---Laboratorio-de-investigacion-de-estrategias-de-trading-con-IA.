"""Explicit manual virtual intents. One SQLite transaction owns approval and posting.

Separate accounts and storage from strategy fills. The existing simulator's pure
accounting/risk transition is reused; a request never becomes an external fill.
"""

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from pathlib import Path
import re
import sqlite3

from trading_ai.tv_contracts import canonical, checksum, decimal_text, fields, instant, label, number, safe_under, strict_json
from trading_ai.tv_simulation import RISK, SimulationLedger, now


def identity(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{32}", value):
        raise ValueError("Identificador manual inválido.")
    return value


def hashes():
    return {name: sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ("conversation_operations.py", "tv_simulation.py", "tv_contracts.py")}


def command(text):
    if not isinstance(text, str) or len(text) > 200:
        raise ValueError("Petición manual demasiado larga.")
    match = re.fullmatch(r"\s*simula\s+(comprar|vender)\s+([0-9]+(?:[.,][0-9]+)?)\s+EUR/USD\s*", text, re.I)
    if not match:
        raise ValueError("Usa «simula comprar 1 EUR/USD» o «simula vender 1 EUR/USD». Las condiciones adicionales requieren otro modo; no se omiten.")
    quantity = number(match[2].replace(",", "."), "cantidad EUR", maximum=Decimal("1e9"), positive=True)
    return {"side": "buy" if match[1].lower() == "comprar" else "sell", "quantity": decimal_text(quantity), "pair": "EUR/USD"}


class ManualOperations:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.path = safe_under(self.root, ".local", "manual-simulation", "ledger.sqlite3")
        self.transition = SimulationLedger(self.root)  # Pure _initial/_apply/_value only; never its database.

    @contextmanager
    def connection(self, write=False):
        safe_under(self.root, ".local", "manual-simulation", "ledger.sqlite3")
        if write: self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.path) if write else self.path.as_uri()+"?mode=ro", uri=not write, timeout=5)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA synchronous=FULL" if write else "PRAGMA query_only=ON")
            conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version == 0 and write:
                if conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone():
                    raise ValueError("Registro manual desconocido; no se reinicia.")
                for sql in (
                    "CREATE TABLE accounts (id TEXT PRIMARY KEY, session TEXT NOT NULL, data TEXT NOT NULL, hash TEXT NOT NULL, engine TEXT NOT NULL, created TEXT NOT NULL)",
                    "CREATE TABLE intents (id TEXT PRIMARY KEY, session TEXT NOT NULL, data TEXT NOT NULL, hash TEXT NOT NULL, request_hash TEXT NOT NULL, status TEXT NOT NULL, approval_id TEXT UNIQUE, approval TEXT, result TEXT)",
                    "CREATE TABLE postings (id INTEGER PRIMARY KEY, account TEXT REFERENCES accounts(id), data TEXT NOT NULL, previous TEXT NOT NULL, hash TEXT NOT NULL)",
                ): conn.execute(sql)
                conn.execute("PRAGMA user_version=1")
            elif version != 1: raise ValueError("Versión del registro manual incompatible.")
            yield conn
            if write: conn.commit()
        except sqlite3.Error as error:
            raise ValueError("No se pudo confirmar el registro manual: " + str(error)) from error
        finally: conn.close()

    def _account(self, conn, account, action=False):
        row = conn.execute("SELECT * FROM accounts WHERE id=?", (identity(account),)).fetchone()
        if row is None: raise KeyError("Cuenta manual inexistente.")
        data = strict_json(row["data"])
        if checksum(data) != row["hash"]: raise ValueError("Cuenta manual alterada.")
        compatible = strict_json(row["engine"]) == hashes()
        if action and not compatible: raise ValueError("El motor manual cambió; conserva esta cuenta y revisa una cuenta nueva.")
        contract = {"account": data["account"]}
        state, chain = self.transition._initial(contract), "0"*64
        for posting in conn.execute("SELECT * FROM postings WHERE account=? ORDER BY id", (account,)):
            record = strict_json(posting["data"])
            if posting["previous"] != chain or checksum({"account": account, "previous": chain, "record": record}) != posting["hash"]:
                raise ValueError("Cadena manual alterada.")
            state, chain = record["state"], posting["hash"]
        return {"id": account, "configuration": data, "state": state, "chain_sha256": chain, "engine_compatible": compatible}

    @staticmethod
    def _intent(conn, session, intent):
        row = conn.execute("SELECT * FROM intents WHERE id=? AND session=?", (identity(intent), identity(session))).fetchone()
        if row is None: raise KeyError("Intención no disponible en esta conversación.")
        data = strict_json(row["data"])
        if checksum(data) != row["hash"]: raise ValueError("Intención manual alterada.")
        result = strict_json(row["result"]) if row["result"] else None
        if row["status"] not in ("awaiting_approval", "cancelled", "applied", "rejected"):
            raise ValueError("Estado manual desconocido.")
        if row["status"] in ("applied", "rejected"):
            if not isinstance(result, dict): raise ValueError("Falta el resultado de la intención.")
            posting = conn.execute("SELECT * FROM postings WHERE account=? AND hash=?", (data["account"], result.get("chain_sha256"))).fetchone()
            if posting is None: raise ValueError("Resultado manual sin asiento.")
            record = strict_json(posting["data"])
            expected = {key: result[key] for key in ("state", "reason", "execution", "mode", "external_order_sent")}
            expected.update(protocol="tiresias_manual_posting_v1", intent=row["id"], intent_sha256=row["hash"],
                            approval=strict_json(row["approval"]), status=row["status"])
            if record != expected or result.get("approval") != expected["approval"] or result.get("intent_sha256") != row["hash"]:
                raise ValueError("Resultado o aprobación manual alterados.")
            if checksum({"account": data["account"], "previous": posting["previous"], "record": record}) != posting["hash"]:
                raise ValueError("Asiento manual alterado.")
        return row, {"id": row["id"], "sha256": row["hash"], "data": data, "status": row["status"], "result": result}

    def overview(self, session):
        identity(session)
        if not self.path.exists(): return {"mode": "manual_virtual", "accounts": [], "intents": [], "risk": dict(RISK)}
        with self.connection() as conn:
            accounts = [self._account(conn, row[0]) for row in conn.execute("SELECT id FROM accounts ORDER BY rowid")]
            intents = [self._intent(conn, session, row[0])[1] for row in conn.execute("SELECT id FROM intents WHERE session=? ORDER BY rowid", (session,))]
        return {"mode": "manual_virtual", "accounts": accounts, "intents": intents, "risk": dict(RISK)}

    def create_account(self, session, body):
        fields(body, ("request_id", "name", "capital", "max_quantity", "cost_rate", "approve_virtual_account"), "cuenta manual")
        account, session = identity(body["request_id"]), identity(session)
        if body["approve_virtual_account"] is not True: raise ValueError("Revisión de cuenta manual requerida.")
        name = label(body["name"])
        settings = {key: decimal_text(number(body[source], source, maximum=Decimal("0.1") if key == "cost_rate" else Decimal("1e9"), positive=key != "cost_rate"))
                    for key, source in (("initial_capital", "capital"), ("quantity", "max_quantity"), ("cost_rate", "cost_rate"))}
        settings.update(id=name, currency="USD")
        data = {"protocol": "tiresias_manual_account_v1", "mode": "manual_virtual", "pair": "EUR/USD", "account": settings, "risk": dict(RISK)}
        with self.connection(True) as conn:
            old = conn.execute("SELECT * FROM accounts WHERE id=?", (account,)).fetchone()
            if old:
                if old["hash"] != checksum(data) or old["session"] != session: raise ValueError("Identidad de cuenta reutilizada.")
                return self._account(conn, account)
            if conn.execute("SELECT count(*) FROM accounts").fetchone()[0] >= 100: raise ValueError("Límite de cien cuentas manuales.")
            for row in conn.execute("SELECT data FROM accounts"):
                if strict_json(row[0])["account"]["id"] == name: raise ValueError("El nombre ya existe; no se reinicia su saldo.")
            conn.execute("INSERT INTO accounts VALUES (?,?,?,?,?,?)", (account, session, canonical(data).decode(), checksum(data), canonical(hashes()).decode(), now()))
            return self._account(conn, account)

    @staticmethod
    def _quote(value, risk):
        fields(value, ("bid", "ask", "at"), "cotización manual BID/ASK")
        bid, ask = number(value["bid"], "BID", positive=True), number(value["ask"], "ASK", positive=True)
        if ask < bid: raise ValueError("ASK no puede ser menor que BID.")
        at = instant(value["at"])
        age = (datetime.fromisoformat(now().replace("Z", "+00:00")) - datetime.fromisoformat(at.replace("Z", "+00:00"))).total_seconds()
        if age < 0 or age > risk["max_price_age_seconds"]: raise ValueError("Cotización futura o demasiado antigua; aporta y revisa otra.")
        return {"bid": decimal_text(bid), "ask": decimal_text(ask), "at": at, "source": "user_supplied_unverified"}

    def _calculate(self, data, account):
        quote = data["quote"]
        event = {"side": data["operation"]["side"], "quantity": data["operation"]["quantity"],
                 "price": quote["ask"] if data["operation"]["side"] == "buy" else quote["bid"], "fee": None,
                 "executed_at": quote["at"], "sequence": account["state"]["last_sequence"]+1}
        state, reason = self.transition._apply(event, account["state"], {"account": account["configuration"]["account"]}, account["configuration"]["risk"])
        if not reason:
            state["price"] = quote["bid"]
            with localcontext(Context(prec=28)):
                self.transition._value(state, account["configuration"]["risk"])
        return {"state": state, "reason": reason, "execution": event, "mode": "manual_virtual", "external_order_sent": False}

    def review(self, session, body):
        fields(body, ("request_id", "account", "text", "quote", "acknowledge_manual"), "revisión manual")
        identity(session); intent = identity(body["request_id"])
        if body["acknowledge_manual"] is not True: raise ValueError("Revisa petición, cuenta y cotización manual.")
        operation = command(body["text"])
        request_hash = checksum({"session": session, "body": body})
        with self.connection(True) as conn:
            old = conn.execute("SELECT request_hash FROM intents WHERE id=?", (intent,)).fetchone()
            if old:
                if old[0] != request_hash: raise ValueError("Identidad manual reutilizada con otros datos.")
                return self._intent(conn, session, intent)[1]
            if conn.execute("SELECT count(*) FROM intents").fetchone()[0] >= 1000: raise ValueError("Límite de mil intenciones manuales.")
            account = self._account(conn, body["account"], action=True)
            quote = self._quote(body["quote"], account["configuration"]["risk"])
            data = {"protocol": "tiresias_manual_intent_v1", "mode": "manual_virtual", "session": session,
                    "account": account["id"], "request_text": body["text"], "operation": operation, "quote": quote,
                    "account_chain_sha256": account["chain_sha256"], "engine_sha256": hashes(), "created": now()}
            data["preview"] = self._calculate(data, account)
            conn.execute("INSERT INTO intents VALUES (?,?,?,?,?,'awaiting_approval',NULL,NULL,NULL)",
                         (intent, session, canonical(data).decode(), checksum(data), request_hash))
            return self._intent(conn, session, intent)[1]

    def approve(self, session, body):
        fields(body, ("request_id", "intent", "intent_sha256", "approve_virtual_execution"), "aprobación manual")
        request = identity(body["request_id"])
        if body["approve_virtual_execution"] is not True: raise ValueError("Ejecución virtual no aprobada.")
        with self.connection(True) as conn:
            row, intent = self._intent(conn, session, body["intent"])
            if body["intent_sha256"] != intent["sha256"]: raise ValueError("Revisión manual sustituida o alterada.")
            duplicate = conn.execute("SELECT id FROM intents WHERE approval_id=?", (request,)).fetchone()
            if duplicate and duplicate[0] != intent["id"]: raise ValueError("Identidad de aprobación reutilizada.")
            if row["status"] in ("applied", "rejected"):
                self._account(conn, intent["data"]["account"])
                return intent
            if row["status"] != "awaiting_approval": raise ValueError("La intención ya no admite aprobación.")
            data = intent["data"]
            if data["engine_sha256"] != hashes(): raise ValueError("El motor cambió; revisa otra intención.")
            account = self._account(conn, data["account"], action=True)
            if data["account_chain_sha256"] != account["chain_sha256"]: raise ValueError("La cuenta cambió; revisa otra intención.")
            self._quote({key: data["quote"][key] for key in ("bid", "ask", "at")}, account["configuration"]["risk"])
            result = self._calculate(data, account)
            status = "rejected" if result["reason"] else "applied"
            approval = {"request": body, "session": session, "approved_at": now(), "intent_sha256": intent["sha256"]}
            record = {"protocol": "tiresias_manual_posting_v1", "intent": intent["id"], "intent_sha256": intent["sha256"],
                      "approval": approval, "status": status, **result}
            chain = account["chain_sha256"]
            hashed = checksum({"account": account["id"], "previous": chain, "record": record})
            conn.execute("INSERT INTO postings (account,data,previous,hash) VALUES (?,?,?,?)", (account["id"], canonical(record).decode(), chain, hashed))
            result.update(chain_sha256=hashed, approval=approval, intent_sha256=intent["sha256"])
            conn.execute("UPDATE intents SET status=?,approval_id=?,approval=?,result=? WHERE id=?", (status, request, canonical(approval).decode(), canonical(result).decode(), intent["id"]))
            return self._intent(conn, session, intent["id"])[1]

    def cancel(self, session, body):
        fields(body, ("request_id", "intent", "intent_sha256"), "cancelación manual")
        identity(body["request_id"])
        with self.connection(True) as conn:
            _, intent = self._intent(conn, session, body["intent"])
            if intent["sha256"] != body["intent_sha256"]: raise ValueError("Huella de intención incompatible.")
            if intent["status"] == "awaiting_approval": conn.execute("UPDATE intents SET status='cancelled' WHERE id=?", (intent["id"],))
            elif intent["status"] != "cancelled": raise ValueError("La ejecución ya terminó; no se deshace mediante cancelación.")
            return self._intent(conn, session, intent["id"])[1]
