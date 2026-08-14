import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command

from ditto_agent.graph.build import build_graph
from ditto_agent.graph.conflict import ConflictChecker
from ditto_agent.schema import ConfirmedCard, DraftContext, InterruptPayload, StartResult

_graph = None


def configure(conflict_checker: ConflictChecker | None = None, checkpointer: BaseCheckpointSaver | None = None) -> None:
    """Call once at process startup to inject a real conflict_checker / checkpointer.

    Without this, start()/resume() build a graph on first use with the placeholder
    conflict checker and an in-memory checkpointer — fine for local dev, not for a
    server that restarts. See agent/README.md.
    """
    global _graph
    _graph = build_graph(conflict_checker=conflict_checker, checkpointer=checkpointer)


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def _read_state(thread_id: str, config: dict) -> StartResult:
    snapshot = _get_graph().get_state(config)
    if snapshot.next:
        task = snapshot.tasks[0]
        payload = InterruptPayload.model_validate(task.interrupts[0].value)
        return StartResult(thread_id=thread_id, status="interrupt", interrupt=payload)
    card = ConfirmedCard.model_validate(snapshot.values["card"])
    return StartResult(thread_id=thread_id, status="done", card=card)


def start(draft: str, context: DraftContext | None = None) -> StartResult:
    ctx = context or DraftContext()
    if ctx.now_iso is None:
        ctx = ctx.model_copy(update={"now_iso": datetime.now(ZoneInfo(ctx.sender_tz)).isoformat()})

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    _get_graph().invoke({"draft": draft, "context": ctx.model_dump()}, config=config)
    return _read_state(thread_id, config)


def resume(thread_id: str, answer: str) -> StartResult:
    config = {"configurable": {"thread_id": thread_id}}
    _get_graph().invoke(Command(resume=answer), config=config)
    return _read_state(thread_id, config)
