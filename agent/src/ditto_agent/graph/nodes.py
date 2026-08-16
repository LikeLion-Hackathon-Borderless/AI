from langgraph.types import interrupt

from ditto_agent.graph.conflict import ConflictChecker
from ditto_agent.graph.state import GraphState
from ditto_agent.llm.client import LLMClient
from ditto_agent.schema import (
    ConfirmedCard,
    ConflictResult,
    DraftContext,
    ExtractionResult,
    InterruptPayload,
)


def extract_node(state: GraphState) -> dict:
    context = DraftContext.model_validate(state["context"])
    result = LLMClient().extract(state["draft"], context)
    return {"extraction": result.model_dump()}


def verify_ambiguities_node(state: GraphState) -> dict:
    extraction = ExtractionResult.model_validate(state["extraction"])
    verified = LLMClient().verify(state["draft"], extraction.ambiguities)
    updated = extraction.model_copy(update={"ambiguities": verified})
    return {"extraction": updated.model_dump()}


def confirm_ambiguities_node(state: GraphState) -> dict:
    extraction = ExtractionResult.model_validate(state["extraction"])
    total = len(extraction.ambiguities)
    confirmed = []
    for i, item in enumerate(extraction.ambiguities, start=1):
        payload = InterruptPayload(step=i, total=total, item=item)
        answer = interrupt(payload.model_dump())
        confirmed.append({"category": item.category, "span": item.span, "answer": answer})

    deadline_confirmed = next((c["answer"] for c in confirmed if c["category"] == "TIME"), None)
    deadline_confirmed = deadline_confirmed or extraction.deadline_raw or "명시된 기한 없음"
    return {"confirmed_ambiguities": confirmed, "deadline_confirmed": deadline_confirmed}


def make_conflict_check_node(conflict_checker: ConflictChecker):
    def conflict_check_node(state: GraphState) -> dict:
        context = DraftContext.model_validate(state["context"])
        result = conflict_checker(state["deadline_confirmed"], context)
        return {"conflict": result.model_dump()}

    return conflict_check_node


def build_card_node(state: GraphState) -> dict:
    extraction = ExtractionResult.model_validate(state["extraction"])
    conflict = ConflictResult.model_validate(state["conflict"])
    confirmed = state.get("confirmed_ambiguities", [])

    decision_status = extraction.decision_status
    interpretation_note = None
    notes: list[str] = []
    time_taken = interp_taken = decision_taken = False

    for c in confirmed:
        # 카테고리당 첫 항목은 카드의 지정된 필드로, 그 이후(같은 카테고리 중복 또는 OTHER)는
        # notes로 — interrupt로 확인은 받되 어떤 항목도 조용히 버려지지 않도록 함
        if c["category"] == "TIME" and not time_taken:
            time_taken = True
        elif c["category"] == "REQUEST_INTENT" and not interp_taken:
            interpretation_note = c["answer"]
            interp_taken = True
        elif c["category"] == "DECISION_STATUS" and not decision_taken:
            decision_status = c["answer"]
            decision_taken = True
        else:
            notes.append(f"[{c['category']}] {c['span']}: {c['answer']}")

    card = ConfirmedCard(
        task=extraction.task,
        assignee=extraction.assignee,
        deadline_confirmed=state["deadline_confirmed"],
        deadline_receiver_local=conflict.receiver_local_time,
        request_type=extraction.request_type,
        decision_status=decision_status,
        interpretation_note=interpretation_note,
        notes=notes,
        conflict=conflict,
        evidence=state["draft"],
    )
    return {"card": card.model_dump()}


def translate_card_node(state: GraphState) -> dict:
    context = DraftContext.model_validate(state["context"])
    if not context.receiver_lang:
        return {}  # Border 02(언어) 대상 아님 — 카드 그대로 둠

    card = ConfirmedCard.model_validate(state["card"])
    translation = LLMClient().translate_card_fields(
        card.task, card.request_type, card.interpretation_note, card.notes, context.receiver_lang
    )
    translated = card.model_copy(
        update={
            "task": translation.task,
            "request_type": translation.request_type,
            "interpretation_note": translation.interpretation_note,
            "notes": translation.notes,
        }
    )
    return {"card": translated.model_dump()}
