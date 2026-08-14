from langgraph.types import interrupt

from ditto_agent.graph.conflict import ConflictChecker
from ditto_agent.graph.state import GraphState
from ditto_agent.llm.client import LLMClient
from ditto_agent.schema import AmbiguityCategory, DraftContext, ConfirmedCard, ConflictResult, ExtractionResult, InterruptPayload


def extract_node(state: GraphState) -> dict:
    context = DraftContext.model_validate(state["context"])
    result = LLMClient().extract(state["draft"], context)
    return {"extraction": result.model_dump()}


def _find_ambiguity(state: GraphState, category: AmbiguityCategory):
    extraction = ExtractionResult.model_validate(state["extraction"])
    return next((a for a in extraction.ambiguities if a.category == category), None)


def time_confirm_node(state: GraphState) -> dict:
    item = _find_ambiguity(state, "TIME")
    if item is None:
        extraction = ExtractionResult.model_validate(state["extraction"])
        return {"time_confirmed": extraction.deadline_raw or "명시된 기한 없음"}
    payload = InterruptPayload(kind="time_confirm", question=item.suggestion, candidates=item.candidates, item=item)
    answer = interrupt(payload.model_dump())
    return {"time_confirmed": answer}


def interp_confirm_node(state: GraphState) -> dict:
    item = _find_ambiguity(state, "REQUEST_INTENT")
    if item is None:
        extraction = ExtractionResult.model_validate(state["extraction"])
        return {"interp_confirmed": extraction.request_type}
    payload = InterruptPayload(kind="interp_confirm", question=item.suggestion, candidates=item.candidates, item=item)
    answer = interrupt(payload.model_dump())
    return {"interp_confirmed": answer}


def make_conflict_check_node(conflict_checker: ConflictChecker):
    def conflict_check_node(state: GraphState) -> dict:
        context = DraftContext.model_validate(state["context"])
        result = conflict_checker(state["time_confirmed"], context)
        return {"conflict": result.model_dump()}

    return conflict_check_node


def build_card_node(state: GraphState) -> dict:
    extraction = ExtractionResult.model_validate(state["extraction"])
    conflict = ConflictResult.model_validate(state["conflict"])
    card = ConfirmedCard(
        task=extraction.task,
        assignee=extraction.assignee,
        deadline_confirmed=state["time_confirmed"],
        deadline_receiver_local=conflict.receiver_local_time,
        request_type=extraction.request_type,
        decision_status=extraction.decision_status,
        interpretation_note=state.get("interp_confirmed"),
        conflict=conflict,
        evidence=state["draft"],
    )
    return {"card": card.model_dump()}
