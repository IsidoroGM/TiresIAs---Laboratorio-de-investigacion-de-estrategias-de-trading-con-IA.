"""A valuation changes equity and risk, never cash, quantity, fees or order count."""

from concurrent.futures import ThreadPoolExecutor

import pytest

from trading_ai.manual_valuation import ManualValuation, age_info, engine_hashes
from trading_ai.tv_simulation import SimulationLedger
from test_conversation_operations import manual, uid, review_body, approval


@pytest.fixture
def position(manual, monkeypatch):
    store, session, account = manual
    clock = {"at": "2026-10-22T12:01:00.000Z"}
    monkeypatch.setattr("trading_ai.manual_valuation.now", lambda: clock["at"])
    monkeypatch.setattr("trading_ai.conversation_operations.now", lambda: clock["at"])
    store.approve(session, approval(store.review(session, review_body(account))))
    return store, session, account, clock


def body(store, session, account, **changes):
    current = next(item for item in store.overview(session)["accounts"] if item["id"] == account)
    return {"request_id": uid(), "account": account, "chain_sha256": current["chain_sha256"], "engine_sha256":engine_hashes(),
            "quote": {"bid": "12", "ask": "12.1", "at": "2026-10-22T12:01:00Z"},
            "approve_manual_valuation": True, **changes}


def test_empty_queries_have_no_storage_or_actions(tmp_path):
    value = ManualValuation(tmp_path).overview(uid())
    assert not value["accounts"] and not value["valuations"] and value["as_of"]
    assert not (tmp_path / ".local").exists()


def test_valuation_changes_only_bid_equity_peak_time_and_risk(position):
    store, session, account, _ = position
    valuation = ManualValuation(store.root)
    before = store.overview(session)["accounts"][0]["state"]
    result = valuation.mark(session, body(store, session, account))
    after = result["record"]["state"]
    assert after["equity"] == "101.9" and after["price"] == "12"
    for key in ("cash", "quantity", "basis", "realized_pnl", "fees", "filled_orders", "last_sequence", "rejections", "estimated_fee_events"):
        assert after[key] == before[key]
    assert not result["record"]["new_fill"] and result["record"]["new_fee"] == "0"
    overview = valuation.overview(session)
    info = overview["accounts"][0]["valuation"]
    assert info["status"] == "within_age_limit" and info["unrealized_pnl_usd"] == "1.9"
    assert not info["market_verified"] and len(overview["valuations"]) == 1
    assert not SimulationLedger(store.root).overview()["accounts"]


@pytest.mark.parametrize("elapsed,status", [(0,"within_age_limit"),(172800,"within_age_limit"),(172801,"stale"),(-1,"future")])
def test_age_boundaries_never_claim_market_authenticity(elapsed, status):
    from datetime import UTC, datetime, timedelta
    base = datetime(2026,10,22,12,tzinfo=UTC)
    state = {"price_at": base.isoformat(), "price": "10", "quantity": "1", "basis": "10.1"}
    value = age_info(state, {"max_price_age_seconds":172800}, (base+timedelta(seconds=elapsed)).isoformat())
    assert value["status"] == status and value["age_seconds"] == elapsed and not value["market_verified"]


def test_missing_price_is_unknown_not_zero(manual):
    store, session, _, = manual
    info = ManualValuation(store.root).overview(session)["accounts"][0]["valuation"]
    assert info["status"] == "missing" and info["age_seconds"] is None and info["unrealized_pnl_usd"] is None


@pytest.mark.parametrize("change", ["approval", "chain", "old", "future", "crossed", "zero", "unknown", "extra", "same_time_other_bid", "backwards"])
def test_unreviewed_or_incompatible_marks_do_not_create_postings(position, change):
    store, session, account, clock = position
    request = body(store, session, account)
    if change == "approval": request["approve_manual_valuation"] = False
    elif change == "chain": request["chain_sha256"] = "0"*64
    elif change == "old": request["quote"]["at"] = "2025-01-01T00:00:00Z"
    elif change == "future": request["quote"]["at"] = "2026-10-22T12:01:01Z"
    elif change == "crossed": request["quote"]["ask"] = "11"
    elif change == "zero": request["quote"]["bid"] = "0"
    elif change == "unknown": request["account"] = uid()
    elif change == "extra": request["side"] = "buy"
    elif change == "same_time_other_bid": request["quote"]["at"] = "2026-10-22T12:00:00Z"
    else: request["quote"]["at"] = "2026-10-22T11:59:59Z"
    before = store.overview(session)
    with pytest.raises((ValueError, KeyError)): ManualValuation(store.root).mark(session, request)
    assert store.overview(session) == before


def test_concurrent_replay_and_restart_preserve_one_mark(position):
    store, session, account, clock = position
    request = body(store, session, account)
    service = ManualValuation(store.root)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: service.mark(session, request), range(2)))
    assert results[0] == results[1]
    clock["at"] = "2026-11-01T00:00:00.000Z"
    assert ManualValuation(store.root).mark(session, request) == results[0]
    assert len(service.overview(session)["valuations"]) == 1
    assert service.overview(session)["accounts"][0]["valuation"]["status"] == "stale"
    with pytest.raises(ValueError): service.mark(session, {**request,"quote":{**request["quote"],"bid":"11"}})
    with pytest.raises(ValueError): service.mark(uid(), request)


def test_a_mark_invalidates_pending_intent_without_creating_a_trade(position):
    store, session, account, _ = position
    pending = store.review(session, review_body(account,text="simula vender 1 EUR/USD"))
    ManualValuation(store.root).mark(session, body(store, session, account))
    with pytest.raises(ValueError, match="cuenta cambió"): store.approve(session, approval(pending))
    assert store.overview(session)["accounts"][0]["state"]["filled_orders"] == 1


def test_changed_valuation_code_invalidates_the_review(position,monkeypatch):
    store,session,account,_=position
    request=body(store,session,account)
    monkeypatch.setattr('trading_ai.manual_valuation.engine_hashes',lambda:{'changed':'1'})
    with pytest.raises(ValueError,match='motor de valoración cambió'):ManualValuation(store.root).mark(session,request)
    assert len(ManualValuation(store.root).overview(session)['valuations'])==0


def test_mark_at_bid_pauses_risk_but_does_not_block_reducing_position(manual, monkeypatch):
    store, session, account = manual
    store.approve(session, approval(store.review(session, review_body(account,quote={"bid":"79","ask":"80","at":"2026-10-22T12:00:00Z"}))))
    monkeypatch.setattr("trading_ai.conversation_operations.now",lambda:"2026-10-22T12:01:00Z")
    monkeypatch.setattr("trading_ai.manual_valuation.now",lambda:"2026-10-22T12:01:00Z")
    service = ManualValuation(store.root)
    result = service.mark(session,body(store,session,account,quote={"bid":"50","ask":"51","at":"2026-10-22T12:01:00Z"}))
    assert result["record"]["state"]["risk_paused"] and result["record"]["state"]["quantity"] == "1"
    sell = store.review(session,review_body(account,text="simula vender 1 EUR/USD",quote={"bid":"50","ask":"51","at":"2026-10-22T12:01:00Z"}))
    assert store.approve(session,approval(sell))["status"] == "applied"


def test_failed_valuation_transaction_rolls_back_and_can_be_replayed(position):
    store, session, account, _ = position
    service = ManualValuation(store.root); request = body(store,session,account)
    before = store.overview(session)
    with store.connection(True) as conn:
        conn.execute("CREATE TRIGGER reject_mark BEFORE INSERT ON postings BEGIN SELECT RAISE(ABORT,'injected mark error'); END")
    with pytest.raises(ValueError,match="injected mark error"): service.mark(session, request)
    assert store.overview(session) == before
    with store.connection(True) as conn: conn.execute("DROP TRIGGER reject_mark")
    assert service.mark(session, request)["record"]["state"]["quantity"] == "1"


def test_altered_mark_is_not_silently_read(position):
    store, session, account, _ = position
    service = ManualValuation(store.root); service.mark(session,body(store,session,account))
    with store.connection(True) as conn: conn.execute("UPDATE postings SET data='{}' WHERE id=(SELECT max(id) FROM postings)")
    with pytest.raises(ValueError): service.overview(session)


def test_http_mark_is_explicit_and_keeps_budgets_and_order_count(tmp_path):
    from test_conversation import FakeProvider, request, auth
    from test_conversation_operations import account_body
    from trading_ai.lab import create_server
    from trading_ai.tv_simulation import now
    import json, threading
    server = create_server(root=tmp_path,port=0,chat_provider=FakeProvider())
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        headers=auth(server)
        _,created=request(server,"/api/chat","POST",json.dumps({"request_id":uid(),"title":"Valuation"}),**headers)
        base="/api/chat/"+created["id"]+"/manual-operations"
        _,account=request(server,base+"/accounts","POST",json.dumps(account_body()),**headers)
        value={"request_id":uid(),"account":account["id"],"chain_sha256":account["chain_sha256"],"engine_sha256":engine_hashes(),"quote":{"bid":"1.1","ask":"1.1002","at":now()},"approve_manual_valuation":True}
        assert request(server,base+"/valuations","POST",json.dumps(value))[0]==403
        assert request(server,base+"/valuations","POST",json.dumps(value),**headers)[0]==202
        overview=request(server,base)[1]
        assert overview["accounts"][0]["state"]["filled_orders"]==0 and overview["accounts"][0]["state"]["cash"]=="100"
        assert len(overview["valuations"])==1
        assert request(server,"/api/chat")[1]["reserved"]=={"model_requests":0,"experiments":0}
    finally:server.shutdown();thread.join();server.server_close()
