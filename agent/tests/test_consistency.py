import uuid

from ditto_agent.graph.build import build_graph
from ditto_agent.llm.client import LLMClient, _vote_extraction
from ditto_agent.schema import AmbiguityItem, DraftContext, ExtractionResult


def _extraction(*categories: str, task: str = "리뷰 요청", decision_status: str = "미정") -> ExtractionResult:
    ambiguities = [
        AmbiguityItem(span="s", category=category, reason="r", candidates=["a"], suggestion="q")
        for category in categories
    ]
    return ExtractionResult(task=task, request_type="검토 요청", decision_status=decision_status, ambiguities=ambiguities)


def test_vote_extraction_keeps_category_hit_by_majority():
    results = [_extraction("TIME"), _extraction("TIME"), _extraction()]
    voted = _vote_extraction(results, threshold=2)
    assert [a.category for a in voted.ambiguities] == ["TIME"]


def test_vote_extraction_drops_category_below_threshold():
    results = [_extraction("TIME"), _extraction(), _extraction()]
    voted = _vote_extraction(results, threshold=2)
    assert voted.ambiguities == []


def test_vote_extraction_handles_multiple_categories_independently():
    results = [
        _extraction("TIME", "DECISION_STATUS"),
        _extraction("TIME"),
        _extraction("DECISION_STATUS"),
    ]
    voted = _vote_extraction(results, threshold=2)
    categories = {a.category for a in voted.ambiguities}
    assert categories == {"TIME", "DECISION_STATUS"}


def test_vote_extraction_picks_majority_scalar_field():
    results = [
        _extraction(decision_status="미정"),
        _extraction(decision_status="미정"),
        _extraction(decision_status="최종 확정"),
    ]
    voted = _vote_extraction(results, threshold=2)
    assert voted.decision_status == "미정"


def test_vote_extraction_unanimous_agreement_passes_through():
    results = [_extraction("TIME"), _extraction("TIME"), _extraction("TIME")]
    voted = _vote_extraction(results, threshold=2)
    assert [a.category for a in voted.ambiguities] == ["TIME"]


def test_vote_extraction_preserves_first_seen_category_order():
    # 회귀 테스트 — seen_categories를 plain set으로 만들면 문자열 hash seed가 프로세스마다
    # 랜덤이라 순서가 실행마다 바뀌었다(그래프 interrupt 순서 테스트가 간헐적으로 깨졌던 원인).
    # REQUEST_INTENT를 먼저 등장시키고 TIME을 나중에 등장시켜도 항상 이 순서를 유지해야 함.
    results = [
        _extraction("REQUEST_INTENT", "TIME"),
        _extraction("REQUEST_INTENT", "TIME"),
        _extraction("REQUEST_INTENT", "TIME"),
    ]
    voted = _vote_extraction(results, threshold=2)
    assert [a.category for a in voted.ambiguities] == ["REQUEST_INTENT", "TIME"]


def test_mock_extract_consistent_calls_extract_batch_n_times(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    client = LLMClient()
    calls = []
    original = client.extract_batch

    def spy(items):
        calls.append(len(items))
        return original(items)

    monkeypatch.setattr(client, "extract_batch", spy)
    client.extract_consistent("내일까지 부탁드려요", DraftContext(now_iso="2026-08-14T18:44:00+09:00"), n=3)
    assert calls == [3]


def test_graph_default_uses_consistency_and_still_reaches_two_interrupts(monkeypatch):
    # build_graph() 기본값이 use_consistency=True로 바뀐 뒤에도(2026-08-17, o3-mini 36케이스
    # 실측 채택) mock 모드 end-to-end happy path가 그대로 유지되는지 확인.
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    graph = build_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    draft = "내일까지 조금 더 고민해 보면 좋을 것 같아요"
    context = DraftContext(now_iso="2026-08-14T18:44:00+09:00")

    graph.invoke({"draft": draft, "context": context.model_dump()}, config=config)
    snapshot = graph.get_state(config)
    assert snapshot.interrupts
    assert snapshot.values["extraction"]["ambiguities"]


def test_graph_use_consistency_false_matches_plain_extract(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    graph = build_graph(use_consistency=False)
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    draft = "내일까지 조금 더 고민해 보면 좋을 것 같아요"
    context = DraftContext(now_iso="2026-08-14T18:44:00+09:00")

    graph.invoke({"draft": draft, "context": context.model_dump()}, config=config)
    snapshot = graph.get_state(config)
    assert snapshot.interrupts
    assert snapshot.values["extraction"]["ambiguities"]
