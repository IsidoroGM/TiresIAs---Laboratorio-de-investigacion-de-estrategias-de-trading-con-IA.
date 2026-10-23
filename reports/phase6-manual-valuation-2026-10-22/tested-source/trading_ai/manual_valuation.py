"""Explicit BID valuation of manual accounts, without fills or schema migration."""

from copy import deepcopy
from datetime import datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
from pathlib import Path

from trading_ai.conversation_operations import ManualOperations, hashes, identity
from trading_ai.tv_contracts import canonical, checksum, fields, strict_json
from trading_ai.tv_simulation import RISK, now


PROTOCOL = "tiresias_manual_valuation_v1"


def engine_hashes():
    return {**hashes(), "manual_valuation.py": sha256(Path(__file__).read_bytes()).hexdigest()}


def age_info(state, risk, as_of):
    """Age describes only the supplied price, never its market authenticity."""
    age = None if state["price_at"] is None else (
        datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        - datetime.fromisoformat(state["price_at"].replace("Z", "+00:00"))).total_seconds()
    status = "missing" if age is None else "future" if age < 0 else "stale" if age > risk["max_price_age_seconds"] else "within_age_limit"
    with localcontext(Context(prec=28)):
        unrealized = None if state["price"] is None else str(Decimal(state["quantity"])*Decimal(state["price"])-Decimal(state["basis"]))
    return {"price_at": state["price_at"], "bid": state["price"], "age_seconds": age, "status": status,
            "unrealized_pnl_usd": unrealized, "source": "user_supplied_unverified", "market_verified": False}


class ManualValuation:
    def __init__(self, root): self.store = ManualOperations(root)

    def overview(self, session):
        identity(session)
        as_of = now()
        if not self.store.path.exists():
            return {"mode": "manual_virtual", "accounts": [], "intents": [], "risk": dict(RISK), "as_of": as_of,
                    "valuations": [], "valuation_engine_sha256": engine_hashes()}
        with self.store.connection() as conn:
            accounts = [self.store._account(conn, row[0]) for row in conn.execute("SELECT id FROM accounts ORDER BY rowid")]
            intents = [self.store._intent(conn, session, row[0])[1] for row in conn.execute("SELECT id FROM intents WHERE session=? ORDER BY rowid", (session,))]
            valuations = []
            rows = conn.execute("SELECT account,data,hash FROM postings WHERE data LIKE ? AND data LIKE ? ORDER BY id DESC LIMIT 200",
                                ('%"protocol":"'+PROTOCOL+'"%', '%"session":"'+session+'"%'))
            for row in rows:
                record = strict_json(row["data"])
                if record.get("protocol") == PROTOCOL and record.get("session") == session:
                    valuations.append({"account": row["account"], "record": record, "chain_sha256": row["hash"]})
            for account in accounts:
                account["valuation"] = age_info(account["state"], account["configuration"]["risk"], as_of)
        return {"mode": "manual_virtual", "accounts": accounts, "intents": intents, "risk": dict(RISK),
                "as_of": as_of, "valuations": list(reversed(valuations)), "valuation_engine_sha256": engine_hashes()}

    @staticmethod
    def _saved(row, body, session):
        record = strict_json(row["data"])
        if record.get("protocol") != PROTOCOL or record.get("request") != body or record.get("session") != session:
            raise ValueError("Identidad de valoración reutilizada con otros datos.")
        if checksum({"account": row["account"], "previous": row["previous"], "record": record}) != row["hash"]:
            raise ValueError("Valoración manual alterada.")
        return {"account": row["account"], "record": record, "chain_sha256": row["hash"]}

    def mark(self, session, body):
        fields(body, ("request_id", "account", "chain_sha256", "engine_sha256", "quote", "approve_manual_valuation"), "valoración manual")
        request, session = identity(body["request_id"]), identity(session)
        if body["approve_manual_valuation"] is not True: raise ValueError("Revisión explícita de la valoración requerida.")
        with self.store.connection(True) as conn:
            # _account verifies the complete chain, even for an idempotent replay.
            account = self.store._account(conn, body["account"])
            previous = conn.execute("SELECT * FROM postings WHERE data LIKE ? LIMIT 2", ('%"valuation_id":"'+request+'"%',)).fetchall()
            if previous:
                if len(previous) != 1: raise ValueError("Identidad de valoración duplicada en el registro.")
                return self._saved(previous[0], body, session)
            account = self.store._account(conn, body["account"], action=True)
            if body["engine_sha256"] != engine_hashes():
                raise ValueError("El motor de valoración cambió; recarga antes de revisar.")
            if body["chain_sha256"] != account["chain_sha256"]:
                raise ValueError("La cuenta cambió; recarga y revisa la valoración.")
            quote = self.store._quote(body["quote"], account["configuration"]["risk"])
            state = deepcopy(account["state"])
            if state["last_at"] is not None and quote["at"] < state["last_at"]:
                raise ValueError("Valoración atrasada; no modifica el historial.")
            if state["price_at"] is not None and quote["at"] == state["price_at"] and quote["bid"] != state["price"]:
                raise ValueError("El instante ya tiene otro BID; aporta una observación posterior.")
            if conn.execute("SELECT count(*) FROM postings WHERE account=?", (account["id"],)).fetchone()[0] >= 10000:
                raise ValueError("Límite de asientos manuales alcanzado.")
            with localcontext(Context(prec=28)):
                state.update(price=quote["bid"], price_at=quote["at"], last_at=quote["at"])
                self.store.transition._value(state, account["configuration"]["risk"])
            record = {"protocol": PROTOCOL, "kind": "valuation", "mode": "manual_virtual", "valuation_id": request,
                      "session": session, "request": deepcopy(body), "quote": quote, "state": state,
                      "engine_sha256": engine_hashes(), "approved_at": now(), "external_order_sent": False,
                      "new_fill": False, "new_fee": "0"}
            chain = account["chain_sha256"]
            hashed = checksum({"account": account["id"], "previous": chain, "record": record})
            conn.execute("INSERT INTO postings (account,data,previous,hash) VALUES (?,?,?,?)",
                         (account["id"], canonical(record).decode(), chain, hashed))
            row = conn.execute("SELECT * FROM postings WHERE hash=? AND account=?", (hashed, account["id"])).fetchone()
            return self._saved(row, body, session)
