import threading
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command

from ditto_agent.graph.build import build_graph
from ditto_agent.graph.conflict import ConflictChecker
from ditto_agent.schema import (
    ConfirmedCard,
    DraftContext,
    InterruptPayload,
    StartResult,
)

_graph = None
_graph_lock = threading.Lock()


# 서버 시작 시 1번 호출해 conflict_checker/checkpointer를 실제 구현으로 교체한다.
# 안 부르면 start()/resume() 첫 호출 때 placeholder conflict_checker + MemorySaver로
# 기본 구성됨 — 로컬 개발용, 재시작 시 스레드 상태가 날아가므로 프로덕션에는 부적합.
def configure(
    conflict_checker: ConflictChecker | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    use_verify: bool = False,
    use_consistency: bool = True,
    consistency_n: int = 3,
) -> None:
    global _graph
    with _graph_lock:
        _graph = build_graph(
            conflict_checker=conflict_checker,
            checkpointer=checkpointer,
            use_verify=use_verify,
            use_consistency=use_consistency,
            consistency_n=consistency_n,
        )


def _get_graph():
    global _graph
    if _graph is None:
        with _graph_lock:
            if _graph is None:
                _graph = build_graph()
    return _graph


def _read_state(thread_id: str, config: dict) -> StartResult:
    snapshot = _get_graph().get_state(config)
    if snapshot.interrupts:
        payload = InterruptPayload.model_validate(snapshot.interrupts[0].value)
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
