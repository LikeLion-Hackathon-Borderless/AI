from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from ditto_agent.graph.conflict import ConflictChecker, default_conflict_checker
from ditto_agent.graph.nodes import build_card_node, extract_node, interp_confirm_node, make_conflict_check_node, time_confirm_node
from ditto_agent.graph.state import GraphState


def build_graph(
    conflict_checker: ConflictChecker | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
):
    graph = StateGraph(GraphState)
    graph.add_node("extract", extract_node)
    graph.add_node("time_confirm", time_confirm_node)
    graph.add_node("interp_confirm", interp_confirm_node)
    graph.add_node("conflict_check", make_conflict_check_node(conflict_checker or default_conflict_checker))
    graph.add_node("build_card", build_card_node)

    graph.set_entry_point("extract")
    graph.add_edge("extract", "time_confirm")
    graph.add_edge("time_confirm", "interp_confirm")
    graph.add_edge("interp_confirm", "conflict_check")
    graph.add_edge("conflict_check", "build_card")
    graph.add_edge("build_card", END)

    return graph.compile(checkpointer=checkpointer or MemorySaver())
