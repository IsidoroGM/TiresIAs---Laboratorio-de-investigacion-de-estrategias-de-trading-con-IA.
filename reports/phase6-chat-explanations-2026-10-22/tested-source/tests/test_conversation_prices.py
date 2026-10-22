"""BID/ASK chat reviews share the existing budget and never grant account authority."""

from copy import deepcopy
from datetime import UTC, date, datetime, timedelta
import gzip
from http.client import HTTPConnection
import json
import shutil
import threading
from uuid import uuid4

import pytest

from trading_ai.ai import AIConfig, ProviderReply
from trading_ai.conversation import ConversationService, DATA_NAME
from trading_ai.conversation_explanation import SCHEMA as EXPLANATION_SCHEMA
from trading_ai.experiments import ExperimentPolicy
from trading_ai.lab import create_server
from trading_ai.market_history import EV_FORMAT, prepare
from trading_ai.tv_contracts import canonical
from trading_ai.tv_simulation import SimulationLedger


def uid(): return uuid4().hex


class Provider:
    config = AIConfig()
    def __init__(self): self.calls = []
    def describe(self): return {"provider": "fake", "model": "fake", "model_digest": "f"*64}
    def complete(self, messages, schema):
        self.calls.append(deepcopy(messages))
        reply = {"answer": "Podemos revisar este cruce y contrastar su comportamiento histórico.", "questions": [], "unsupported": [],
                 "proposal": {"strategy": "sma", "fast_window": 15, "slow_window": 45, "hypothesis": "Contrastar SMA15/45 con la base."}}
        if schema == EXPLANATION_SCHEMA:
            facts = json.loads(messages[-1]["content"].rsplit("Evidencia verificada: ", 1)[1])
            reply = {"criterion": facts["criterion"], "assessment": facts["assessment"], "topics": ["criterion", "costs"]}
        return ProviderReply(json.dumps(reply), "fake", {"input_tokens": 100, "output_tokens": 50, "api_cost_usd": "0"})


def make_prices(root, *, days=90, gap=False):
    start = datetime(2025, 1, 1, tzinfo=UTC)
    rows = []
    for index in range(days):
        price = 1+((index % 30)-15)**2/10000
        rows.append({"ts": int((start+timedelta(days=index)).timestamp()),
                     **{key: price for key in ("o", "h", "l", "c")},
                     **{key: price+0.0001 for key in ("ao", "ah", "al", "ac")}, "v": 1})
    if gap: rows.insert(1, {**rows[0], "ts": rows[0]["ts"]+7200})
    prepare(inputs=[{"name": "2025.json.gz", "side": "BOTH", "body": gzip.compress(canonical(rows))}],
        source_format=EV_FORMAT, year=2025, start_date="2025-01-01",
        end_date=(start+timedelta(days=days)).date().isoformat(), output=root / ".local/dukascopy/sample")


@pytest.fixture
def chat(tmp_path):
    make_prices(tmp_path)
    provider = Provider()
    service = ConversationService(tmp_path, provider=provider)
    session = service.create(uid(), "BID/ASK")['id']
    try: yield service, session, provider
    finally: service.close()


def review(service, session, **changes):
    latest = service.detail(session)["revisions"]
    body = {"request_id": uid(), "previous": latest[-1]["id"] if latest else None,
        "candidate": {"strategy": "sma", "fast_window": 15, "slow_window": 45, "hypothesis": "Contrastar otro cruce de medias."},
        "baseline": {"strategy": "sma", "fast_window": 20, "slow_window": 60},
        "policy": {"initial_capital": "1000", "quantity": "1", "cost_rate": "0.001"},
        "dataset": "sample", "source_sha256": service.price_source("sample")["sha256"],
        "criterion": "higher_return_without_more_drawdown", "acknowledge_rules": True, **changes}
    return service.revise_prices(session, body)


def submit(service, session, revision, **changes):
    return service.submit(session, "experiment", {"request_id": uid(), "revision": revision["id"],
        "revision_sha256": revision["hash"], "approve_historical": True, **changes})


def wait(service, session, job):
    with service._condition:
        assert service._condition.wait_for(lambda: any(row["id"] == job["id"] and row["state"] not in ("queued", "running")
            for row in service.detail(session)["jobs"]), 10)
    return next(row for row in service.detail(session)["jobs"] if row["id"] == job["id"])


def test_price_queries_do_not_create_chat_or_run_model_or_strategy(tmp_path, monkeypatch):
    make_prices(tmp_path)
    service = ConversationService(tmp_path, provider=Provider())
    def forbidden(*args, **kwargs): raise AssertionError("Query cannot calculate")
    monkeypatch.setattr("trading_ai.conversation_prices.simulate", forbidden)
    try:
        assert service.price_sources()["datasets"][0]["id"] == "sample"
        assert service.price_source("sample")["daily_sessions"] == 90
        assert not (tmp_path / ".local/conversations").exists()
        assert not service.provider.calls
    finally: service.close()


def test_review_approval_two_runs_and_evidence_explanation_without_ecb(chat):
    service, session, provider = chat
    ledger = SimulationLedger(service.root)
    before = ledger.overview()
    job = service.submit(session, "message", {"request_id": uid(), "text": "Propón SMA15/45 para precios BID/ASK.", "context_ids": [], "result_job": None})
    assert wait(service, session, job)["state"] == "completed"
    revision = review(service, session)
    assert not (service.root / ".local/chat-price-experiments").exists()
    experiment = submit(service, session, revision)
    assert wait(service, session, experiment)["state"] == "completed"
    result = service.result(session, experiment["id"])
    assert result["source"]["kind"] == "prices_bidask" and result["source"]["observations"] == 90
    assert result["baseline"]["strategy"] == "SMA20/SMA60" and result["candidate"]["strategy"] == "SMA15/SMA45"
    for role in ("baseline", "candidate"):
        assert result["price_calculations"][role]["configuration"]["quantity"] == "1"
        assert result["price_calculations"][role]["configuration"]["buy_quote"] == "ask"
    assert not result["accounting_processed"] and ledger.overview() == before
    explanation = service.submit(session, "message", {"request_id": uid(), "text": "Explica cualitativamente el resultado.", "context_ids": [], "result_job": experiment["id"]})
    assert wait(service, session, explanation)["state"] == "completed"
    assert "BID/ASK" in provider.calls[-1][-1]["content"]
    assert service.overview()["reserved"] == {"model_requests": 2, "experiments": 1}


@pytest.mark.parametrize("change", ["ema", "same", "cost", "quantity", "window", "unknown", "unapproved"])
def test_unsupported_or_unreviewed_price_controls_are_rejected(chat, change):
    service, session, _ = chat
    changes = {}
    if change == "ema": changes["candidate"] = {"strategy": "ema", "fast_window": 15, "slow_window": 45, "hypothesis": "EMA revisada."}
    elif change == "same": changes["baseline"] = {"strategy": "sma", "fast_window": 15, "slow_window": 45}
    elif change == "cost": changes["policy"] = {"initial_capital": "1000", "quantity": "1", "cost_rate": "0.2"}
    elif change == "quantity": changes["policy"] = {"initial_capital": "1000", "quantity": "0", "cost_rate": "0.001"}
    elif change == "window": changes["baseline"] = {"strategy": "sma", "fast_window": 20, "slow_window": 253}
    elif change == "unknown": changes["stop_loss"] = "0.02"
    else: changes["acknowledge_rules"] = False
    with pytest.raises((ValueError, TypeError)):
        review(service, session, **changes)
    assert service.overview()["reserved"]["experiments"] == 0
    assert not service.detail(session)["revisions"]


@pytest.mark.parametrize("kwargs", [{"days": 10}, {"gap": True}])
def test_insufficient_or_gapped_prices_cannot_be_approved(tmp_path, kwargs):
    make_prices(tmp_path, **kwargs)
    service = ConversationService(tmp_path, provider=Provider())
    try:
        session = service.create(uid(), "Quality")["id"]
        with pytest.raises(ValueError, match="insuficiente|huecos"):
            review(service, session)
        assert not service.detail(session)["revisions"] and service.overview()["reserved"]["experiments"] == 0
    finally: service.close()


def test_stale_revision_and_missing_approval_do_not_reserve(chat):
    service, session, _ = chat
    first = review(service, session)
    with pytest.raises(ValueError, match="aprobar"):
        submit(service, session, first, approve_historical=False)
    review(service, session, candidate={"strategy": "sma", "fast_window": 10, "slow_window": 30, "hypothesis": "Otra comparación."})
    with pytest.raises(ValueError, match="sustituida"):
        submit(service, session, first)
    assert service.overview()["reserved"]["experiments"] == 0


def test_changed_source_before_approval_or_queued_execution_does_not_calculate(chat):
    service, session, _ = chat
    revision = review(service, session)
    path = service.root / ".local/dukascopy/sample/raw/00.json.gz"
    raw = path.read_bytes()
    path.write_bytes(raw+b"changed")
    with pytest.raises(ValueError): submit(service, session, revision)
    assert service.overview()["reserved"]["experiments"] == 0
    path.write_bytes(raw)
    with service._condition:
        job = submit(service, session, revision)
        path.write_bytes(raw+b"changed")
    assert wait(service, session, job)["state"] == "failed"
    assert service.overview()["reserved"]["experiments"] == 1
    assert not (service.root / ".local/chat-price-experiments").exists()


def test_changed_engine_requires_a_new_review(chat, monkeypatch):
    service, session, _ = chat
    revision = review(service, session)
    monkeypatch.setattr("trading_ai.conversation.conversation_hashes", lambda: {"changed": "0"*64})
    with pytest.raises(ValueError, match="Código"):
        submit(service, session, revision)
    assert service.overview()["reserved"]["experiments"] == 0


def test_replay_and_duplicate_alias_do_not_repeat_comparison(chat):
    service, session, _ = chat
    revision = review(service, session)
    request_id = uid()
    first = submit(service, session, revision, request_id=request_id)
    assert wait(service, session, first)["state"] == "completed"
    assert submit(service, session, revision, request_id=request_id)["id"] == first["id"]
    shutil.copytree(service.root / ".local/dukascopy/sample", service.root / ".local/dukascopy/alias")
    second = review(service, session, dataset="alias", source_sha256=service.price_source("alias")["sha256"],
        policy={"initial_capital": "1000.00", "quantity": "1.0", "cost_rate": "0.0010"},
        criterion="lower_drawdown_without_lower_return")
    with pytest.raises(ValueError, match="intento reservado"):
        submit(service, session, second)
    assert service.overview()["reserved"]["experiments"] == 1


@pytest.mark.parametrize("filename", ["results.json", "input-manifest.json", "input-daily.json", "approval.json"])
def test_result_and_approval_copies_are_verified_without_recalculation(chat, filename, monkeypatch):
    service, session, _ = chat
    job = submit(service, session, review(service, session))
    finished = wait(service, session, job)
    assert finished["state"] == "completed"
    def forbidden(*args, **kwargs): raise AssertionError("Read cannot calculate")
    monkeypatch.setattr("trading_ai.conversation_prices.simulate", forbidden)
    assert service.result(session, job["id"])["protocol"] == "conversation_price_result_v1"
    path = service.root / ".local/chat-price-experiments" / finished["result"]["directory"] / filename
    path.write_bytes(path.read_bytes()+b"changed")
    with pytest.raises(ValueError): service.result(session, job["id"])


def test_other_conversation_cannot_approve_or_attach_price_result(chat):
    service, session, _ = chat
    revision = review(service, session)
    other = service.create(uid(), "Other")["id"]
    with pytest.raises(KeyError): submit(service, other, revision)
    job = submit(service, session, revision)
    assert wait(service, session, job)["state"] == "completed"
    with pytest.raises(ValueError, match="no disponible"):
        service.submit(other, "message", {"request_id": uid(), "text": "Explain", "context_ids": [], "result_job": job["id"]})


def test_interrupted_price_job_is_not_replayed_and_keeps_reservation(chat, monkeypatch):
    service, session, _ = chat
    job = submit(service, session, review(service, session))
    assert wait(service, session, job)["state"] == "completed"
    service.close()
    with service.connection(True) as conn:
        conn.execute("UPDATE jobs SET state='running' WHERE id=?", (job["id"],))
    def forbidden(*args, **kwargs): raise AssertionError("Interrupted jobs must not replay")
    monkeypatch.setattr("trading_ai.conversation_prices.simulate", forbidden)
    reopened = ConversationService(service.root, provider=Provider())
    try:
        assert reopened.detail(session)["jobs"][0]["state"] == "needs_review"
        assert reopened.overview()["reserved"]["experiments"] == 1
        assert not reopened.provider.calls
    finally: reopened.close()


def test_prices_and_ecb_use_the_same_persisted_four_comparison_budget(chat):
    service, session, _ = chat
    for fast in (2, 3, 4):
        job = submit(service, session, review(service, session,
            candidate={"strategy": "sma", "fast_window": fast, "slow_window": 10, "hypothesis": "Comparación de integración."}))
        assert wait(service, session, job)["state"] == "completed"
    path = service.root / "data/raw" / DATA_NAME
    path.parent.mkdir(parents=True)
    cubes = ''.join(f'<Cube time="{date(2020,1,1)+timedelta(days=i)}"><Cube currency="USD" rate="{1+i%3}"/></Cube>' for i in range(30))
    path.write_text('<Envelope xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref"><Cube>'+cubes+'</Cube></Envelope>', encoding="utf-8")
    rev = service.revise(session, {"request_id": uid(), "previous": service.detail(session)["revisions"][-1]["id"],
        "candidate": {"strategy": "ema", "fast_window": 2, "slow_window": 4, "hypothesis": "Comparar EMA."},
        "policy": ExperimentPolicy(fast_window=2, slow_window=3).parameters(), "first_date": "2020-01-01", "last_date": "2020-01-30",
        "criterion": "higher_return_without_more_drawdown", "source_sha256": service.source()["sha256"], "acknowledge_rules": True})
    job = submit(service, session, rev)
    assert wait(service, session, job)["state"] == "completed"
    revision = review(service, session)
    with pytest.raises(ValueError, match="global"):
        submit(service, session, revision)
    service.close()
    reopened = ConversationService(service.root, provider=Provider())
    try:
        assert reopened.overview()["reserved"]["experiments"] == 4
        with pytest.raises(ValueError, match="global"): submit(reopened, session, revision)
    finally: reopened.close()


@pytest.mark.parametrize("identity", ["../outside", None, ".."])
def test_source_identity_does_not_accept_arbitrary_paths(tmp_path, identity):
    service = ConversationService(tmp_path)
    try:
        with pytest.raises(ValueError): service.price_source(identity)
        assert not (tmp_path / ".local").exists()
    finally: service.close()


def test_http_price_review_and_approval_use_existing_origin_and_token(tmp_path):
    make_prices(tmp_path)
    server = create_server(root=tmp_path, port=0, chat_provider=Provider())
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05})
    thread.start()
    def request(method, path, body=None, headers=None):
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        try:
            connection.request(method, path, body=canonical(body) if body else None, headers=headers or {})
            response = connection.getresponse()
            return response.status, json.loads(response.read())
        finally: connection.close()
    try:
        overview = request('GET','/api/chat')[1]
        source = request('GET','/api/chat/price-sources/sample')[1]
        assert request('GET','/api/chat/price-sources')[1]['datasets'][0]['id'] == 'sample'
        headers = {'Origin':f'http://127.0.0.1:{server.server_port}','Content-Type':'application/json','X-Tiresias-Action':overview['action_token']}
        session = request('POST','/api/chat',{'request_id':uid(),'title':'HTTP'},headers)[1]['id']
        body = {'request_id':uid(),'previous':None,'candidate':{'strategy':'sma','fast_window':15,'slow_window':45,'hypothesis':'Revisión HTTP.'},
            'baseline':{'strategy':'sma','fast_window':20,'slow_window':60},'policy':{'initial_capital':'1000','quantity':'1','cost_rate':'0.001'},
            'dataset':'sample','source_sha256':source['sha256'],'criterion':'higher_return_without_more_drawdown','acknowledge_rules':True}
        path = '/api/chat/'+session+'/price-revisions'
        assert request('POST',path,body,{'Content-Type':'application/json'})[0] == 403
        assert request('POST',path,body,{**headers,'X-Tiresias-Action':'wrong'})[0] == 403
        code, rev = request('POST',path,body,headers)
        assert code == 202
        code, job = request('POST','/api/chat/'+session+'/experiments',{'request_id':uid(),'revision':rev['id'],'revision_sha256':rev['hash'],'approve_historical':True},headers)
        assert code == 202 and wait(server.conversation,session,job)['state'] == 'completed'
        code, result = request('GET','/api/chat/'+session+'/results/'+job['id'])
        assert code == 200 and result['source']['kind'] == 'prices_bidask'
    finally:
        server.shutdown();thread.join(timeout=5);server.server_close()
