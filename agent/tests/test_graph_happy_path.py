import uuid

from langgraph.types import Command

from ditto_agent.graph.build import build_graph
from ditto_agent.schema import ConfirmedCard, DraftContext, InterruptPayload


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def test_happy_path_two_interrupts_then_card(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    graph = build_graph()
    config = _config(str(uuid.uuid4()))
    draft = "내일까지 조금 더 고민해 보면 좋을 것 같아요"
    context = DraftContext(now_iso="2026-08-14T18:44:00+09:00")

    graph.invoke({"draft": draft, "context": context.model_dump()}, config=config)
    snapshot = graph.get_state(config)
    assert snapshot.interrupts
    first = InterruptPayload.model_validate(snapshot.interrupts[0].value)
    assert (first.step, first.total) == (1, 2)
    assert first.item.category == "TIME"

    graph.invoke(Command(resume=first.item.candidates[0]), config=config)
    snapshot = graph.get_state(config)
    assert snapshot.interrupts
    second = InterruptPayload.model_validate(snapshot.interrupts[0].value)
    assert (second.step, second.total) == (2, 2)
    assert second.item.category == "REQUEST_INTENT"

    graph.invoke(Command(resume=second.item.candidates[0]), config=config)
    snapshot = graph.get_state(config)
    assert not snapshot.interrupts

    card = ConfirmedCard.model_validate(snapshot.values["card"])
    assert card.deadline_confirmed == first.item.candidates[0]
    assert card.interpretation_note == second.item.candidates[0]
    assert card.conflict.within_working_hours is False  # LA 새벽 시간대
    assert card.notes == []


def test_no_ambiguity_skips_interrupt_entirely(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    graph = build_graph()
    config = _config(str(uuid.uuid4()))
    context = DraftContext(now_iso="2026-08-14T10:00:00+09:00")

    graph.invoke({"draft": "8/20 18:00 KST까지 리뷰 부탁드립니다.", "context": context.model_dump()}, config=config)
    snapshot = graph.get_state(config)
    assert not snapshot.interrupts  # 모호성 없으면 경고를 억제 — 바로 카드까지 진행

    card = ConfirmedCard.model_validate(snapshot.values["card"])
    assert "까지" in card.deadline_confirmed
    assert card.deadline_confirmed != "명시된 기한 없음"
