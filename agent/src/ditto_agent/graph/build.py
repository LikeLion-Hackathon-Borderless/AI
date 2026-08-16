from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from ditto_agent.graph.conflict import ConflictChecker, default_conflict_checker
from ditto_agent.graph.nodes import (
    build_card_node,
    confirm_ambiguities_node,
    extract_node,
    make_conflict_check_node,
    translate_card_node,
    verify_ambiguities_node,
)
from ditto_agent.graph.state import GraphState


def build_graph(
    conflict_checker: ConflictChecker | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    use_verify: bool = False,
):
    # use_verify 기본값 False — 2026-08-17 gpt-5-mini 실측(docs/survey-results-analysis.md
    # 10절)에서 verify_ambiguities_node가 precision을 0.679→0.500으로 악화시키는 게 확인돼
    # (recall은 소폭만 오름, FP가 거의 2배) 기본 파이프라인에서 뺐다. 노드/LLMClient.verify()
    # 자체는 테스트로 검증된 채 남겨두고, 프롬프트를 더 보수적으로 튜닝한 뒤
    # `build_graph(use_verify=True)`로 재검증하는 걸 다음 단계로 남김.
    graph = StateGraph(GraphState)
    graph.add_node("extract", extract_node)
    graph.add_node("confirm_ambiguities", confirm_ambiguities_node)
    graph.add_node("conflict_check", make_conflict_check_node(conflict_checker or default_conflict_checker))
    graph.add_node("build_card", build_card_node)
    graph.add_node("translate_card", translate_card_node)

    graph.set_entry_point("extract")
    if use_verify:
        graph.add_node("verify_ambiguities", verify_ambiguities_node)
        graph.add_edge("extract", "verify_ambiguities")
        graph.add_edge("verify_ambiguities", "confirm_ambiguities")
    else:
        graph.add_edge("extract", "confirm_ambiguities")
    graph.add_edge("confirm_ambiguities", "conflict_check")
    graph.add_edge("conflict_check", "build_card")
    graph.add_edge("build_card", "translate_card")
    graph.add_edge("translate_card", END)

    return graph.compile(checkpointer=checkpointer or MemorySaver())
