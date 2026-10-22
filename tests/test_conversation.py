"""La conversación no concede permisos ni repite efectos tras fallos o recargas."""

from copy import deepcopy
from datetime import date, timedelta
import http.client
import json
from pathlib import Path
import threading
from uuid import uuid4

import pytest

from trading_ai.ai import AIConfig, ProviderError, ProviderReply
from trading_ai.conversation import ConversationService, DATA_NAME, LIMITS, digest, strict, validate_candidate
from trading_ai import conversation_explanation
from trading_ai.conversation_provider import CHAT_SCHEMA, ConversationProvider, check_context
from trading_ai.experiments import ExperimentPolicy
from trading_ai.lab import create_server
from trading_ai.lab_query import LabQuery


def uid(): return uuid4().hex


REPLY = {"answer": "Podemos estudiar un cruce de medias largas. Revisa las reglas y los controles antes de calcular.",
         "questions": [], "unsupported": [],
         "proposal": {"strategy": "ema", "fast_window": 2, "slow_window": 4, "hypothesis": "Un cruce más lento podría reducir las oscilaciones."}}


class FakeProvider:
    config = AIConfig()
    def __init__(self, reply=None):
        self.reply = deepcopy(reply or REPLY)
        self.calls = []
        self.entered, self.release = threading.Event(), threading.Event()
        self.release.set()

    def describe(self):
        return {"provider": "fake", "model": "fake-local", "model_digest": "f"*64}

    def complete(self, messages, schema):
        self.calls.append(deepcopy(messages)); self.entered.set()
        assert self.release.wait(10)
        if isinstance(self.reply, Exception): raise self.reply
        return ProviderReply(json.dumps(self.reply, ensure_ascii=False), "fake-local",
                             {"input_tokens": 100, "output_tokens": 50, "api_cost_usd": "0"})


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "data/raw" / DATA_NAME
    path.parent.mkdir(parents=True)
    days = []
    for i in range(30):
        price = [1, 2, 3, 2, 1, 3][i % 6]
        days.append(f'<Cube time="{date(2020, 1, 1)+timedelta(days=i)}"><Cube currency="USD" rate="{price}"/><Cube currency="GBP" rate="0.8"/><Cube currency="JPY" rate="150"/><Cube currency="CHF" rate="1.1"/></Cube>')
    path.write_text('<Envelope xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref"><Cube>'+''.join(days)+'</Cube></Envelope>', encoding="utf-8")
    return tmp_path


@pytest.fixture
def chat(source):
    provider = FakeProvider()
    service = ConversationService(source, provider=provider)
    session = service.create(uid(), "Prueba")['id']
    try: yield service, session, provider
    finally: provider.release.set(); service.close()


def message(**changes):
    return {"request_id": uid(), "text": "Estudiemos una estrategia EMA", "context_ids": [], "result_job": None, **changes}


def wait(service, session, job):
    with service._condition:
        assert service._condition.wait_for(lambda: any(row["id"] == job["id"] and row["state"] not in ("queued", "running") for row in service.detail(session)["jobs"]), 10)
    return next(row for row in service.detail(session)["jobs"] if row["id"] == job["id"])


def revision(service, session, **changes):
    detail = service.detail(session)
    body = {"request_id": uid(), "previous": detail["revisions"][-1]["id"] if detail["revisions"] else None,
            "candidate": deepcopy(REPLY["proposal"]), "policy": ExperimentPolicy(fast_window=2, slow_window=3).parameters(),
            "first_date": "2020-01-01", "last_date": "2020-01-30", "criterion": "higher_return_without_more_drawdown",
            "source_sha256": service.source()["sha256"], "acknowledge_rules": True, **changes}
    return service.revise(session, body)


def experiment(service, session, rev, **changes):
    return service.submit(session, "experiment", {"request_id": uid(), "revision": rev["id"],
                          "revision_sha256": rev["hash"], "approve_historical": True, **changes})


def test_gets_do_not_initialize_or_infer(source):
    provider = FakeProvider()
    service = ConversationService(source, provider=provider)
    try:
        assert not service.overview()["sessions"]
        assert service.source()["first_date"] == "2020-01-01"
        assert not (source / ".local").exists()
        assert not provider.calls
    finally: service.close()


def test_message_replay_and_restart_preserve_history_and_usage(chat):
    service, session, provider = chat
    body = message()
    job = service.submit(session, "message", body)
    assert wait(service, session, job)["state"] == "completed"
    assert service.submit(session, "message", body)["id"] == job["id"]
    assert len(provider.calls) == 1
    detail = service.detail(session)
    assert [row["role"] for row in detail["messages"]] == ["user", "assistant"]
    assert detail["revisions"][0]["data"]["status"] == "pending_human_review"
    assert detail["jobs"][0]["usage"]["input_tokens"] == 100
    assert detail["jobs"][0]["result"]["provider"]["model_digest"] == "f"*64
    service.close()
    reopened = ConversationService(service.root, provider=provider)
    try:
        assert reopened.detail(session)["messages"] == detail["messages"]
        assert reopened.overview()["reserved"]["model_requests"] == 1
        assert len(provider.calls) == 1
    finally: reopened.close()


def test_request_identity_cannot_change_payload(chat):
    service, session, _ = chat
    body = message()
    job = service.submit(session, "message", body); wait(service, session, job)
    with pytest.raises(ValueError, match="contenido distinto"):
        service.submit(session, "message", {**body, "text": "otra cosa"})


@pytest.mark.parametrize("changes", [{"text": ""}, {"text": "x"*801}, {"context_ids": [uid()]}, {"result_job": "../../README.md"}, {"tool": "buy"}])
def test_invalid_messages_never_reserve_or_call(chat, changes):
    service, session, provider = chat
    with pytest.raises((ValueError, KeyError)): service.submit(session, "message", message(**changes))
    assert service.overview()["reserved"]["model_requests"] == 0
    assert not provider.calls


def test_only_selected_context_is_sent(chat):
    service, session, provider = chat
    first = service.submit(session, "message", message()); wait(service, session, first)
    messages = service.detail(session)["messages"]
    second = service.submit(session, "message", message(text="¿Qué falta?", context_ids=[messages[0]["id"]]))
    done = wait(service, session, second)
    assert provider.calls[-1][1]["content"] == messages[0]["content"]
    assert len(provider.calls[-1]) == 3
    assert done["result"]["context"]["excluded_messages"] == 1


def test_context_overflow_rejects_without_truncating_or_reserving(chat):
    service, session, provider = chat
    ids = []
    with service.connection(True) as conn:
        for _ in range(8):
            ident = uid(); ids.append(ident)
            conn.execute("INSERT INTO messages VALUES (?,?,?,?,?,?)", (ident, session, "user", "á"*800, None, "2020"))
    with pytest.raises(ValueError, match="contexto elegido"):
        service.submit(session, "message", message(context_ids=ids))
    assert not provider.calls
    assert service.overview()["reserved"]["model_requests"] == 0


@pytest.mark.parametrize("reply", [ProviderError("Desconectado"), {**REPLY, "proposal": {**REPLY["proposal"], "strategy": "short"}}, {**REPLY, "tool": "buy"}])
def test_failed_reply_keeps_attempt_and_unknown_usage(chat, reply):
    service, session, provider = chat; provider.reply = reply
    job = service.submit(session, "message", message())
    result = wait(service, session, job)
    assert result["state"] == "failed"
    assert not service.detail(session)["revisions"]
    assert service.overview()["reserved"]["model_requests"] == 1
    if isinstance(reply, ProviderError): assert result["usage"] is None
    else: assert result["result"]["raw"]


def test_unsupported_rules_stay_incomplete_and_cannot_run(chat):
    service, session, provider = chat
    provider.reply["unsupported"] = ["stop-loss"]
    job = service.submit(session, "message", message()); wait(service, session, job)
    rev = service.detail(session)["revisions"][-1]
    assert rev["data"]["status"] == "incomplete"
    with pytest.raises(ValueError, match="no está lista"): experiment(service, session, rev)


def test_explicit_review_then_historical_result_is_catalogued_and_verified(chat):
    service, session, provider = chat
    sent = service.submit(session, "message", message()); wait(service, session, sent)
    rev = revision(service, session)
    job = experiment(service, session, rev)
    assert wait(service, session, job)["state"] == "completed"
    result = service.result(session, job["id"])
    assert result["policy"]["pair"] == "EUR/USD"
    assert result["source"]["observations"] == 30
    assert result["revision_sha256"] == rev["hash"]
    detail = LabQuery(service.root).detail(result["catalog_id"])
    assert len(detail["accounts"]) == 2
    assert detail["hypothesis"] == REPLY["proposal"]["hypothesis"]
    assert len(provider.calls) == 1  # historical execution itself never infers
    with service.connection() as conn:
        saved = strict(conn.execute("SELECT result FROM jobs WHERE id=?", (job["id"],)).fetchone()[0])
    path = service.root / ".local/chat-experiments" / saved["directory"] / "results.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="alterado"): service.result(session, job["id"])
    with pytest.raises(ValueError, match="alterado"): service.submit(session, "message", message(result_job=job["id"]))


@pytest.mark.parametrize("changes", [{"acknowledge_rules": False}, {"candidate": {**REPLY["proposal"], "fast_window": True}}, {"candidate": {**REPLY["proposal"], "slow_window": 1}}, {"source_sha256": "0"*64}, {"last_date": "2030-01-01"}, {"first_date": "2019-01-01"}])
def test_review_rejects_invalid_rules_controls_or_source(chat, changes):
    service, session, _ = chat
    with pytest.raises((ValueError, TypeError)): revision(service, session, **changes)
    assert not service.detail(session)["revisions"]


def test_superseded_revision_and_missing_approval_cannot_run(chat):
    service, session, _ = chat
    old = revision(service, session); current = revision(service, session)
    with pytest.raises(ValueError): experiment(service, session, old)
    with pytest.raises(ValueError): experiment(service, session, current, approve_historical=False)
    assert service.overview()["reserved"]["experiments"] == 0


def test_same_comparison_is_not_reopened_in_another_session(chat):
    service, session, _ = chat
    rev = revision(service, session); job = experiment(service, session, rev); wait(service, session, job)
    other = service.create(uid(), "Otra")['id']
    other_revision = revision(service, other, candidate={**REPLY["proposal"], "hypothesis": "Otra redacción"})
    with pytest.raises(ValueError, match="ya tiene un intento"): experiment(service, other, other_revision)
    assert service.overview()["reserved"]["experiments"] == 1


def test_decimal_aliases_and_changed_criterion_do_not_repeat_calculations(chat):
    service, session, _ = chat
    rev = revision(service, session); job = experiment(service, session, rev); wait(service, session, job)
    policy = {**ExperimentPolicy(fast_window=2,slow_window=3).parameters(), "cost_rate": "0.0010", "initial_capital": "1000.0"}
    rev = revision(service, session, policy=policy, criterion="lower_drawdown_without_lower_return")
    with pytest.raises(ValueError, match="ya tiene un intento"): experiment(service, session, rev)
    assert service.overview()["reserved"]["experiments"] == 1


def test_experiment_budget_does_not_reset_in_new_session(chat):
    service, session, _ = chat
    for slow in range(4,8):
        rev = revision(service, session, candidate={**REPLY["proposal"], "slow_window":slow})
        job = experiment(service, session, rev); assert wait(service, session, job)["state"] == "completed"
    other = service.create(uid(), "Nuevo nombre")['id']
    rev = revision(service, other, candidate={**REPLY["proposal"], "slow_window":8})
    with pytest.raises(ValueError, match="global"): experiment(service, other, rev)
    assert service.overview()["reserved"]["experiments"] == 4


def test_insufficient_history_is_rejected_before_any_calculation(chat):
    service, session, _ = chat
    with pytest.raises(ValueError, match="Historia insuficiente"):
        revision(service, session, last_date="2020-01-04")
    assert service.overview()["reserved"]["experiments"] == 0


def test_queue_is_bounded_and_cancelled_attempts_remain_reserved(chat):
    service, session, provider = chat; provider.release.clear()
    first = service.submit(session, "message", message()); assert provider.entered.wait(5)
    for i in range(LIMITS["queued_jobs"]-1):
        other = service.create(uid(), "Cola "+str(i))['id']; service.submit(other,"message",message())
    other = service.create(uid(), "Fuera de cola")['id']
    with pytest.raises(ValueError, match="Cola"): service.submit(other,"message",message())
    provider.release.set(); wait(service,session,first)


def test_cancel_keeps_budget_and_does_not_claim_running_request_was_stopped(chat):
    service, session, provider = chat; provider.release.clear()
    running = service.submit(session, "message", message()); assert provider.entered.wait(5)
    service.cancel(session, running["id"])
    other = service.create(uid(), "Cola")['id']
    queued = service.submit(other, "message", message())
    service.cancel(other, queued["id"])
    provider.release.set()
    assert wait(service, session, running)["state"] == "completed_after_cancel"
    assert wait(service, other, queued)["state"] == "cancelled"
    assert len(provider.calls) == 1
    assert service.overview()["reserved"]["model_requests"] == 2


def test_active_session_and_second_server_are_blocked(chat):
    service, session, provider = chat; provider.release.clear()
    job = service.submit(session, "message", message()); assert provider.entered.wait(5)
    with pytest.raises(ValueError, match="activo"): service.submit(session, "message", message())
    other = ConversationService(service.root, provider=FakeProvider())
    try:
        with pytest.raises(ValueError, match="Otro servidor"): other.create(uid(), "Otro servidor")
        assert other.detail(session)["jobs"][0]["state"] == "running"
    finally: other.close(); provider.release.set(); wait(service, session, job)


def test_restart_never_replays_unresolved_jobs(chat):
    service, session, provider = chat
    job = service.submit(session, "message", message()); wait(service, session, job)
    service.close()
    with service.connection(True) as conn: conn.execute("UPDATE jobs SET state='running' WHERE id=?", (job["id"],))
    other = ConversationService(service.root, provider=provider)
    try:
        other.create(uid(), "Después del reinicio")
        assert other.detail(session)["jobs"][0]["state"] == "needs_review"
        assert len(provider.calls) == 1
        assert other.overview()["reserved"]["model_requests"] == 1
    finally: other.close()


def test_persisted_context_tampering_is_rejected_before_inference(chat):
    service, session, provider = chat
    with service._condition:
        job = service.submit(session, "message", message())
        with service.connection(True) as conn:
            row = strict(conn.execute("SELECT payload FROM jobs WHERE id=?", (job["id"],)).fetchone()[0])
            row["prepared"]["messages"][0]["content"] = "buy"
            conn.execute("UPDATE jobs SET payload=? WHERE id=?", (json.dumps(row), job["id"]))
    assert wait(service, session, job)["state"] == "failed"
    assert not provider.calls


def test_global_budget_survives_new_session_and_restart(chat):
    service, session, provider = chat
    for _ in range(LIMITS["model_requests"]):
        provider.reply = {**REPLY, "proposal": None}
        job = service.submit(session, "message", message()); wait(service, session, job)
    other = service.create(uid(), "Otra sesión")['id']
    with pytest.raises(ValueError, match="global"): service.submit(other, "message", message())
    assert len(provider.calls) == LIMITS["model_requests"]


def test_strict_json_rejects_duplicates_and_nonfinite():
    for raw in ('{"text":1,"text":2}', '{"value":NaN}'):
        with pytest.raises(ValueError): strict(raw)


def test_ema_hypothesis_cannot_become_sma_without_explicit_correction():
    with pytest.raises(ValueError, match="contradicen"):
        validate_candidate({**REPLY["proposal"], "strategy": "sma", "hypothesis": "Cruce EMA15/EMA45"})


def test_result_discussion_uses_registered_criterion_and_checked_explanation(chat):
    service, session, provider = chat
    rev = revision(service, session); job = experiment(service, session, rev); wait(service, session, job)
    result = service.result(session, job["id"])
    facts = conversation_explanation.facts(result)
    provider.reply = {"criterion": facts["criterion"], "assessment": facts["assessment"], "topics": ["criterion"]}
    discussion = service.submit(session, "message", message(result_job=job["id"]))
    done = wait(service, session, discussion)
    assert done["state"] == "completed"
    assert done["result"]["evidence"]["job"] == job["id"]
    assert done["result"]["explanation"]["status"] == "consistent"
    assert "Criterio revisado" in service.detail(session)["messages"][-1]["content"]
    assert '"criterion":"higher_return_without_more_drawdown"' in provider.calls[-1][-1]["content"]


def test_corrupt_database_is_reported_without_reinitializing(source):
    path = source / ".local/conversations/chat.sqlite3"
    path.parent.mkdir(parents=True); path.write_bytes(b"invalid sqlite")
    with pytest.raises(ValueError, match="no se reiniciará"): ConversationService(source)
    assert path.read_bytes() == b"invalid sqlite"


def test_source_change_after_review_blocks_reservation(chat):
    service, session, _ = chat
    rev = revision(service, session)
    path = service.root / "data/raw" / DATA_NAME
    path.write_text(path.read_text().replace('rate="1"','rate="1.01"'),encoding="utf-8")
    with pytest.raises(ValueError, match="fuente cambiados"): experiment(service, session, rev)
    assert service.overview()["reserved"]["experiments"] == 0


def test_provider_rejects_truncation_and_changed_model():
    calls = []
    def transport(method, path, body):
        calls.append((method, path, body))
        if path == "/api/version": return {"version": "0.40.6"}
        if path == "/api/tags": return {"models": [{"name": "qwen3.5:4b", "digest": "a"*64}]}
        assert body["truncate"] is False and body["shift"] is False
        return {"model": "qwen3.5:4b", "done": True, "done_reason": "length", "prompt_eval_count": 100, "eval_count": 384}
    provider = ConversationProvider(transport=transport)
    with pytest.raises(ProviderError, match="truncadas"):
        provider.complete([{"role": "system", "content": "Solo JSON"}, {"role": "user", "content": "Hola"}])
    assert len([row for row in calls if row[0] == "POST"]) == 1
    with pytest.raises(ValueError): check_context([{"role": "user", "content": "x"*10000}])


@pytest.fixture
def http_chat(source):
    provider = FakeProvider(); server = create_server(root=source, port=0, chat_provider=provider)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try: yield server, provider
    finally: provider.release.set(); server.shutdown(); thread.join(); server.server_close()


def request(server, path, method="GET", body=None, **headers):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
    try:
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse(); raw = response.read()
        return response.status, json.loads(raw) if raw else None
    finally: connection.close()


def auth(server):
    status, overview = request(server, "/api/chat"); assert status == 200
    return {"Origin": f"http://127.0.0.1:{server.server_port}", "Content-Type": "application/json", "X-Tiresias-Action": overview["action_token"]}


@pytest.mark.parametrize("headers", [{}, {"Origin": "null"}, {"Origin": "https://attacker.example"}, {"X-Tiresias-Action": "bad"}, {"Host": "attacker.example"}, {"Sec-Fetch-Site": "cross-site"}])
def test_post_requires_local_origin_and_action_token(http_chat, headers):
    server, provider = http_chat
    allowed = auth(server)
    if not headers: allowed.pop("Origin")
    else: allowed.update(headers)
    assert request(server, "/api/chat", "POST", json.dumps({"request_id": uid(), "title": "Hola"}), **allowed)[0] == 403
    assert not provider.calls


def test_http_invalid_payloads_and_gets_have_no_side_effects(http_chat):
    server, provider = http_chat
    headers = auth(server)
    assert request(server, "/api/chat", "POST", "x"*17000, **headers)[0] == 413
    assert request(server, "/api/chat", "POST", '{"title":1,"title":2}', **headers)[0] == 422
    assert request(server, "/api/chat/../../README.md")[0] == 404
    assert not (server.conversation.root / ".local").exists()
    assert not provider.calls


def test_reads_remain_available_during_model_work(http_chat):
    server, provider = http_chat; provider.release.clear()
    headers = auth(server)
    status, session = request(server, "/api/chat", "POST", json.dumps({"request_id": uid(), "title": "Trabajo"}), **headers)
    assert status == 202
    path = "/api/chat/"+session["id"]
    status, job = request(server, path+"/messages", "POST", json.dumps(message()), **headers); assert status == 202
    assert provider.entered.wait(5)
    assert request(server, "/api/home")[0] == 200
    assert request(server, path)[1]["jobs"][0]["state"] == "running"
    provider.release.set(); wait(server.conversation, session["id"], job)
