from ditto_agent import configure, resume, start
from ditto_agent.schema import StartResult


def test_interrupt_payload_matches_doc_json_schema(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    configure()
    result = start("내일까지 검토해주세요")

    assert isinstance(result, StartResult)
    assert result.status == "interrupt"
    item = result.interrupt.item
    # 핸드오프 문서 5절: span/category/reason/candidates/suggestion
    assert item.span
    assert item.category in ("TIME", "REQUEST_INTENT", "DECISION_STATUS", "OTHER")
    assert item.reason
    assert item.candidates
    assert item.suggestion


def test_resume_with_same_thread_id_advances_to_next_interrupt(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    configure()
    result = start("내일까지 조금 더 고민해 보면 좋을 것 같아요")
    assert result.status == "interrupt"
    assert result.interrupt.item.category == "TIME"
    thread_id = result.thread_id

    result = resume(thread_id, result.interrupt.item.candidates[0])
    assert result.thread_id == thread_id
    assert result.status == "interrupt"
    assert result.interrupt.item.category == "REQUEST_INTENT"

    result = resume(thread_id, result.interrupt.item.candidates[0])
    assert result.status == "done"
    assert result.card is not None
