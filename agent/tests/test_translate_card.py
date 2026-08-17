import uuid

from langgraph.types import Command

from ditto_agent.graph.build import build_graph
from ditto_agent.schema import ConfirmedCard, DraftContext


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def test_receiver_lang_none_leaves_card_untouched(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    graph = build_graph()
    config = _config(str(uuid.uuid4()))
    context = DraftContext(now_iso="2026-08-15T10:00:00+09:00")  # receiver_lang 미지정

    graph.invoke({"draft": "8/20 18:00 KST까지 리뷰 부탁드립니다.", "context": context.model_dump()}, config=config)
    card = ConfirmedCard.model_validate(graph.get_state(config).values["card"])
    assert not card.task.startswith("[")  # 번역 접두어가 안 붙어야 함(mock 번역기는 "[lang] " 접두)


def test_receiver_lang_set_translates_free_text_fields(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    graph = build_graph()
    config = _config(str(uuid.uuid4()))
    context = DraftContext(now_iso="2026-08-15T10:00:00+09:00", receiver_lang="en")

    graph.invoke({"draft": "8/20 18:00 KST까지 리뷰 부탁드립니다.", "context": context.model_dump()}, config=config)
    card = ConfirmedCard.model_validate(graph.get_state(config).values["card"])
    assert card.task.startswith("[en] ")
    assert card.request_type.startswith("[en] ")
    # 구조화된 필드는 번역 대상이 아님 — 그대로 유지, 번역 접두어 없음
    assert not card.deadline_confirmed.startswith("[")


def test_translate_with_ambiguity_resume_flow(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    graph = build_graph()
    config = _config(str(uuid.uuid4()))
    context = DraftContext(now_iso="2026-08-15T10:00:00+09:00", receiver_lang="en")

    graph.invoke({"draft": "내일까지 조금 더 고민해 보면 좋을 것 같아요", "context": context.model_dump()}, config=config)
    snapshot = graph.get_state(config)
    first = snapshot.interrupts[0].value
    graph.invoke(Command(resume=first["item"]["candidates"][0]), config=config)
    snapshot = graph.get_state(config)
    second = snapshot.interrupts[0].value
    graph.invoke(Command(resume=second["item"]["candidates"][0]), config=config)

    card = ConfirmedCard.model_validate(graph.get_state(config).values["card"])
    assert card.interpretation_note.startswith("[en] ")
