from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from ditto_agent.graph.conflict import ConflictChecker, default_conflict_checker
from ditto_agent.graph.nodes import (
    build_card_node,
    confirm_ambiguities_node,
    make_conflict_check_node,
    make_extract_node,
    translate_card_node,
    verify_ambiguities_node,
)
from ditto_agent.graph.state import GraphState


def build_graph(
    conflict_checker: ConflictChecker | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    use_verify: bool = False,
    use_consistency: bool = False,
    consistency_n: int = 3,
    use_rag: bool = False,
):
    # use_verify 기본값 False — 2026-08-17 gpt-5-mini 실측(docs/survey-results-analysis.md
    # 10절)에서 verify_ambiguities_node가 precision을 0.679→0.500으로 악화시키는 게 확인돼
    # (recall은 소폭만 오름, FP가 거의 2배) 기본 파이프라인에서 뺐다. 노드/LLMClient.verify()
    # 자체는 테스트로 검증된 채 남겨두고, 프롬프트를 더 보수적으로 튜닝한 뒤
    # `build_graph(use_verify=True)`로 재검증하는 걸 다음 단계로 남김.
    #
    # use_consistency 기본값 False(2026-08-17 최종 확정) — golden.json의 고정
    # few-shot leave-one-out 유출을 다 막고 6회 반복 측정(pooled n=108)한 결과, 진짜
    # recall/precision 트레이드오프로 확인됨: 끔=recall 0.810/precision 0.761, 켬=recall
    # 0.746/precision 0.825(survey-results-analysis.md §18). 오해 방지 도구는 놓치는 것(FN)이
    # 조용히 실패하는 게 과탐지(FP)보다 치명적이라 recall을 우선 — 게다가 켬은 응답을 n배
    # 생성해야 해서 지연시간도 늘어남. precision을 더 우선해야 하는 사용 사례가 있으면
    # `use_consistency=True`로 언제든 켤 수 있음(옵션은 그대로 남아있음).
    #
    # use_rag 기본값 False — 36케이스 전체 실측에서 recall/precision이 크게 올라(1.000/0.875)
    # 한때 True로 바꿨으나, golden.json ambiguous 케이스의 76%(13/17)가 RAG로 **자기 자신의
    # 원본 판단기준표 항목을 few-shot으로 그대로 받아오는** 것으로 확인돼(golden set이
    # culture_criteria.py 항목의 패러프레이즈라서) 정답 유출에 가까운 측정으로 판단, False로
    # 되돌림(2026-08-17, docs/survey-results-analysis.md 17-4절). 리키지 없는 재검증 방법을
    # 찾기 전까진 이 상태 유지.
    graph = StateGraph(GraphState)
    graph.add_node("extract", make_extract_node(use_consistency, consistency_n, use_rag))
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
