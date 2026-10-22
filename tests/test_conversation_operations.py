"""Manual approval is atomic, price-bound, separate from strategy fills and replay-safe."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from uuid import uuid4

import pytest

from trading_ai.conversation_operations import ManualOperations, command
from trading_ai.tv_contracts import canonical
from trading_ai.tv_simulation import SimulationLedger


def uid(): return uuid4().hex


def account_body(**changes):
    return {"request_id": uid(), "name": "manual-test", "capital": "100", "max_quantity": "1",
            "cost_rate": "0.01", "approve_virtual_account": True, **changes}


def review_body(account, **changes):
    return {"request_id": uid(), "account": account, "text": "simula comprar 1 EUR/USD",
            "quote": {"bid": "9.9", "ask": "10", "at": "2026-10-22T12:00:00Z"},
            "acknowledge_manual": True, **changes}


def approval(intent, **changes):
    return {"request_id": uid(), "intent": intent["id"], "intent_sha256": intent["sha256"],
            "approve_virtual_execution": True, **changes}


@pytest.fixture
def manual(tmp_path, monkeypatch):
    monkeypatch.setattr("trading_ai.conversation_operations.now", lambda: "2026-10-22T12:00:00.000Z")
    store, session = ManualOperations(tmp_path), uid()
    account = store.create_account(session, account_body())
    return store, session, account["id"]


def test_query_never_initializes_or_processes(tmp_path):
    assert ManualOperations(tmp_path).overview(uid())["accounts"] == []
    assert not (tmp_path / ".local").exists()


@pytest.mark.parametrize("text", ["compra ahora", "simula comprar 1 EUR/USD con stop 5", "simula vender 1 BTC/USD",
    "simula comprar 0 EUR/USD", "simula comprar -1 EUR/USD", "simula comprar 1 EUR/USD y vender 2 EUR/USD", "simula comprar NaN EUR/USD"])
def test_unrepresented_conditions_or_invalid_commands_are_never_silently_dropped(text):
    with pytest.raises(ValueError): command(text)


def test_spanish_decimal_normalizes_without_changing_quantity():
    assert command(" SIMULA COMPRAR 0,25 EUR/USD ") == {"side": "buy", "quantity": "0.25", "pair": "EUR/USD"}


def test_review_does_not_execute_then_bidask_cost_and_realized_are_exact(manual):
    store, session, account = manual
    body = review_body(account)
    intent = store.review(session, body)
    assert store.overview(session)["accounts"][0]["state"]["cash"] == "100"
    assert store.review(session, body) == intent
    buy = store.approve(session, approval(intent))
    assert buy["status"] == "applied"
    state = buy["result"]["state"]
    assert state["cash"] == "89.9" and state["quantity"] == "1" and state["equity"] == "99.8"
    assert state["price"] == "9.9" and state["fees"] == "0.1"
    sell = store.review(session, review_body(account, text="simula vender 1 EUR/USD", quote={"bid": "12", "ask": "12.1", "at": body["quote"]["at"]}))
    closed = store.approve(session, approval(sell))["result"]["state"]
    assert closed["cash"] == closed["equity"] == "101.78" and closed["quantity"] == "0"
    assert closed["realized_pnl"] == "1.78" and closed["fees"] == "0.22"
    assert not SimulationLedger(store.root).overview()["accounts"]
    assert not (store.root / ".local/simulation").exists()


@pytest.mark.parametrize("changes", [{"approve_virtual_account": False}, {"capital": "NaN"}, {"max_quantity": "0"},
    {"cost_rate": "0.11"}, {"name": "../account"}, {"risk": {}}, {"capital": 100}])
def test_invalid_account_cannot_create_funds(tmp_path, changes):
    with pytest.raises(ValueError): ManualOperations(tmp_path).create_account(uid(), account_body(**changes))


def test_account_replay_does_not_reset_funds_and_duplicate_name_is_rejected(manual):
    store, session, account = manual
    with store.connection() as conn:
        row = conn.execute("SELECT data FROM accounts WHERE id=?", (account,)).fetchone()
    config = json.loads(row[0])["account"]
    body = account_body(request_id=account, capital=config["initial_capital"], max_quantity=config["quantity"], cost_rate=config["cost_rate"])
    store.approve(session, approval(store.review(session, review_body(account))))
    assert store.create_account(session, body)["state"]["cash"] == "89.9"
    with pytest.raises(ValueError, match="ya existe"): store.create_account(session, account_body())


@pytest.mark.parametrize("quote", [
    {"bid": "10", "ask": "9", "at": "2026-10-22T12:00:00Z"},
    {"bid": "10", "ask": "11", "at": "2025-01-01T00:00:00Z"},
    {"bid": "10", "ask": "11", "at": "2026-10-22T12:00:01Z"},
    {"bid": "10", "ask": "Infinity", "at": "2026-10-22T12:00:00Z"},
])
def test_quote_crossed_old_future_or_invalid_is_rejected_before_review(manual, quote):
    store, session, account = manual
    with pytest.raises(ValueError): store.review(session, review_body(account, quote=quote))
    assert not store.overview(session)["intents"]


@pytest.mark.parametrize("text,reason", [("simula comprar 2 EUR/USD", "quantity_limit"), ("simula vender 1 EUR/USD", "insufficient_position")])
def test_independent_risk_rejections_are_recorded_once_without_a_fill(manual, text, reason):
    store, session, account = manual
    intent = store.review(session, review_body(account, text=text))
    assert intent["data"]["preview"]["reason"] == reason
    assert store.overview(session)["accounts"][0]["state"]["rejections"] == 0
    result = store.approve(session, approval(intent))
    assert result["status"] == "rejected" and result["result"]["reason"] == reason
    assert result["result"]["state"]["cash"] == "100" and result["result"]["state"]["filled_orders"] == 0
    assert store.approve(session, approval(intent)) == result


def test_insufficient_cash_is_not_bypassed_by_price_or_preview(manual):
    store, session, account = manual
    intent = store.review(session, review_body(account, quote={"bid": "200", "ask": "201", "at": "2026-10-22T12:00:00Z"}))
    assert store.approve(session, approval(intent))["result"]["reason"] == "insufficient_cash"


def test_pyramiding_and_risk_pause_still_apply(manual):
    store, session, account = manual
    store.approve(session, approval(store.review(session, review_body(account))))
    second = store.review(session, review_body(account))
    assert store.approve(session, approval(second))["result"]["reason"] == "pyramiding_not_allowed"


def test_bid_valuation_triggers_drawdown_pause_but_allows_reducing_position(manual):
    store, session, account = manual
    def reviewed(text, bid, ask):
        return store.review(session, review_body(account, text=text, quote={"bid": bid, "ask": ask, "at": "2026-10-22T12:00:00Z"}))
    bought = store.approve(session, approval(reviewed("simula comprar 1 EUR/USD", "50", "80")))
    assert bought["result"]["state"]["risk_paused"] and bought["result"]["state"]["equity"] == "69.2"
    sold = store.approve(session, approval(reviewed("simula vender 1 EUR/USD", "50", "51")))
    assert sold["status"] == "applied" and sold["result"]["state"]["quantity"] == "0"
    assert store.approve(session, approval(reviewed("simula comprar 1 EUR/USD", "9.9", "10")))["result"]["reason"] == "risk_paused"


def test_stale_account_snapshot_cannot_execute_other_pending_intent(manual):
    store, session, account = manual
    first = store.review(session, review_body(account)); second = store.review(session, review_body(account))
    store.approve(session, approval(first))
    with pytest.raises(ValueError, match="cuenta cambió"): store.approve(session, approval(second))
    assert store.overview(session)["intents"][1]["status"] == "awaiting_approval"


def test_explicit_approval_hash_session_and_cancel_are_enforced(manual):
    store, session, account = manual
    intent = store.review(session, review_body(account))
    with pytest.raises(ValueError): store.approve(session, approval(intent, approve_virtual_execution=False))
    with pytest.raises(ValueError): store.approve(session, approval(intent, intent_sha256="0"*64))
    with pytest.raises(KeyError): store.approve(uid(), approval(intent))
    body = {"request_id": uid(), "intent": intent["id"], "intent_sha256": intent["sha256"]}
    assert store.cancel(session, body)["status"] == "cancelled"
    assert store.cancel(session, body)["status"] == "cancelled"
    with pytest.raises(ValueError): store.approve(session, approval(intent))
    assert store.overview(session)["accounts"][0]["state"]["cash"] == "100"


def test_expired_quote_and_changed_engine_require_another_review(manual, monkeypatch):
    store, session, account = manual
    intent = store.review(session, review_body(account))
    monkeypatch.setattr("trading_ai.conversation_operations.now", lambda: "2026-10-25T12:00:00.000Z")
    with pytest.raises(ValueError, match="antigua"): store.approve(session, approval(intent))
    monkeypatch.setattr("trading_ai.conversation_operations.hashes", lambda: {"changed": "1"})
    with pytest.raises(ValueError, match="motor cambió"): store.approve(session, approval(intent))


def test_concurrent_and_restart_replays_never_double_post(manual):
    store, session, account = manual
    intent = store.review(session, review_body(account)); body = approval(intent)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: store.approve(session, body), range(2)))
    assert results[0] == results[1]
    reopened = ManualOperations(store.root)
    assert reopened.approve(session, body) == results[0]
    with store.connection() as conn: assert conn.execute("SELECT count(*) FROM postings").fetchone()[0] == 1
    with pytest.raises(ValueError): store.cancel(session, {"request_id": uid(), "intent": intent["id"], "intent_sha256": intent["sha256"]})


def test_failed_commit_rolls_back_approval_and_posting_together(manual):
    store, session, account = manual
    intent = store.review(session, review_body(account)); body = approval(intent)
    with store.connection(True) as conn:
        conn.execute("CREATE TRIGGER deny_update BEFORE UPDATE ON intents BEGIN SELECT RAISE(ABORT,'injected failure'); END")
    with pytest.raises(ValueError, match="injected failure"): store.approve(session, body)
    assert store.overview(session)["accounts"][0]["state"]["cash"] == "100"
    assert store.overview(session)["intents"][0]["status"] == "awaiting_approval"
    with store.connection(True) as conn: conn.execute("DROP TRIGGER deny_update")
    assert store.approve(session, body)["status"] == "applied"


@pytest.mark.parametrize("target", ["account", "intent", "posting", "result"])
def test_altered_inputs_chain_or_result_are_not_silently_used(manual, target):
    store, session, account = manual
    intent = store.review(session, review_body(account))
    if target in ("posting", "result"): store.approve(session, approval(intent))
    with store.connection(True) as conn:
        if target == "account": conn.execute("UPDATE accounts SET data='{}'")
        elif target == "intent": conn.execute("UPDATE intents SET data='{}'")
        elif target == "posting": conn.execute("UPDATE postings SET data='{}'")
        else:
            value = json.loads(conn.execute("SELECT result FROM intents").fetchone()[0]); value["state"]["cash"] = "999999"
            conn.execute("UPDATE intents SET result=?", (canonical(value).decode(),))
    with pytest.raises((ValueError, KeyError)): store.overview(session)


def test_http_guards_and_manual_actions_leave_model_and_experiment_budgets_unchanged(tmp_path):
    from test_conversation import FakeProvider, request, auth
    from trading_ai.lab import create_server
    import threading
    provider = FakeProvider(); server = create_server(root=tmp_path, port=0, chat_provider=provider)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        headers = auth(server)
        status, created = request(server, "/api/chat", "POST", json.dumps({"request_id": uid(), "title": "Manual"}), **headers)
        assert status == 202
        base = "/api/chat/"+created["id"]+"/manual-operations"
        assert request(server, base)[1]["accounts"] == []
        body = account_body()
        assert request(server, base+"/accounts", "POST", json.dumps(body))[0] == 403
        status, account = request(server, base+"/accounts", "POST", json.dumps(body), **headers)
        assert status == 202
        from trading_ai.tv_simulation import now
        body = review_body(account["id"], quote={"bid": "1.1", "ask": "1.1002", "at": now()})
        status, intent = request(server, base+"/reviews", "POST", json.dumps(body), **headers)
        assert status == 202 and intent["status"] == "awaiting_approval"
        assert request(server, base+"/approvals", "POST", json.dumps(approval(intent)), **headers)[1]["status"] == "applied"
        assert request(server, "/api/chat")[1]["reserved"] == {"model_requests": 0, "experiments": 0}
        assert not provider.calls and not SimulationLedger(tmp_path).overview()["accounts"]
    finally: server.shutdown(); thread.join(); server.server_close()
