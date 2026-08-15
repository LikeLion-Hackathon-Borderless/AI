from ditto_agent.graph.nodes import build_card_node
from ditto_agent.schema import ConfirmedCard, ConflictResult, ExtractionResult

_EXTRACTION = ExtractionResult(
    task="문서 검토",
    assignee="Alex",
    deadline_raw="내일까지",
    request_type="검토 요청",
    decision_status="제안",
    ambiguities=[],
)
_CONFLICT = ConflictResult(receiver_local_time="2026-08-15T02:00:00-07:00", within_working_hours=False)


def _state(confirmed: list[dict]) -> dict:
    return {
        "draft": "원문",
        "extraction": _EXTRACTION.model_dump(),
        "conflict": _CONFLICT.model_dump(),
        "deadline_confirmed": "2026-08-15T18:00:00+09:00",
        "confirmed_ambiguities": confirmed,
    }


def test_decision_status_and_other_categories_are_not_dropped():
    confirmed = [
        {"category": "DECISION_STATUS", "span": "확인했습니다", "answer": "승인합니다"},
        {"category": "OTHER", "span": "침묵", "answer": "이의 없음(암묵적 동의)"},
    ]
    card = ConfirmedCard.model_validate(build_card_node(_state(confirmed))["card"])
    assert card.decision_status == "승인합니다"
    assert card.notes == ["[OTHER] 침묵: 이의 없음(암묵적 동의)"]


def test_duplicate_category_beyond_first_goes_to_notes():
    # 첫 TIME 항목은 deadline_confirmed로 이미 소비된 것으로 간주(confirm_ambiguities_node가
    # 그 값을 그대로 state["deadline_confirmed"]에 반영) — 두 번째부터가 진짜 "중복" 케이스.
    confirmed = [
        {"category": "TIME", "span": "C1", "answer": "2026-08-15T18:00:00+09:00"},
        {"category": "REQUEST_INTENT", "span": "A", "answer": "방향 유지"},
        {"category": "REQUEST_INTENT", "span": "B", "answer": "재검토 요청"},
        {"category": "TIME", "span": "C2", "answer": "2026-08-16T09:00:00+09:00"},
    ]
    card = ConfirmedCard.model_validate(build_card_node(_state(confirmed))["card"])
    assert card.interpretation_note == "방향 유지"
    assert card.notes == ["[REQUEST_INTENT] B: 재검토 요청", "[TIME] C2: 2026-08-16T09:00:00+09:00"]
