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
    return make_extract_node()(state)


def make_extract_node(use_consistency: bool = False, n: int = 3, use_rag: bool = False):
    # use_consistency=True면 단발 extract() 대신 extract_consistent()(n회 독립 추출 후
    # 카테고리 만장일치 채택)를 쓴다 — 2026-08-17 o3-mini 36케이스 전체 실측(recall=0.857,
    # precision=0.750, 이번 세션 최고 균형 결과, docs/survey-results-analysis.md 13-1/16절)
    # 으로 verify-loop과 달리 채택하기로 함. API 요청 수는 여전히 1번(배치 크기가 n일 뿐)이라
    # RPD 부담은 그대로지만, 한 번의 응답이 n배 더 길어져 지연시간은 늘어난다는 점은 감안할 것.
    # use_rag 기본 False — golden.json ambiguous 케이스의 76%가 RAG로 자기 자신의 원본
    # 판단기준표 항목을 few-shot으로 받아오는 유출 문제가 확인돼(17-4절) 채택을 되돌림.
    def node(state: GraphState) -> dict:
        context = DraftContext.model_validate(state["context"])
        client = LLMClient(use_rag=use_rag)
        result = (
            client.extract_consistent(state["draft"], context, n=n)
            if use_consistency
            else client.extract(state["draft"], context)
        )
        return {"extraction": result.model_dump()}

    return node


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
