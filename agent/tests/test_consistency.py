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

    def spy(items, few_shot_ids=None):
        calls.append(len(items))
        return original(items, few_shot_ids=few_shot_ids)

    monkeypatch.setattr(client, "extract_batch", spy)
    client.extract_consistent("내일까지 부탁드려요", DraftContext(now_iso="2026-08-14T18:44:00+09:00"), n=3)
    assert calls == [3]


def test_graph_default_no_consistency_still_reaches_two_interrupts(monkeypatch):
    # build_graph() 기본값이 use_consistency=False로 최종 확정된 뒤(유출 없이 6회 반복·
    # pooled n=108로 재측정한 결과 진짜 recall/precision 트레이드오프로 확인돼 recall 우선)
    # mock 모드 end-to-end happy path가 그대로 유지되는지 확인.
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    graph = build_graph()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    draft = "내일까지 조금 더 고민해 보면 좋을 것 같아요"
    context = DraftContext(now_iso="2026-08-14T18:44:00+09:00")

    graph.invoke({"draft": draft, "context": context.model_dump()}, config=config)
    snapshot = graph.get_state(config)
    assert snapshot.interrupts
    assert snapshot.values["extraction"]["ambiguities"]


def test_graph_use_consistency_true_still_reaches_two_interrupts(monkeypatch):
    # precision을 더 우선해야 하는 사용 사례를 위해 옵션은 남겨뒀으니(기본값만 False),
    # 명시적으로 켰을 때도 mock 모드 end-to-end happy path가 깨지지 않는지 확인.
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    graph = build_graph(use_consistency=True)
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    draft = "내일까지 조금 더 고민해 보면 좋을 것 같아요"
    context = DraftContext(now_iso="2026-08-14T18:44:00+09:00")

    graph.invoke({"draft": draft, "context": context.model_dump()}, config=config)
    snapshot = graph.get_state(config)
    assert snapshot.interrupts
    assert snapshot.values["extraction"]["ambiguities"]


def test_graph_use_rag_true_still_reaches_two_interrupts(monkeypatch):
    # use_rag 기본값은 False로 유지 중(golden set 76%가 RAG로 자기 자신의 원본 판단기준표
    # 항목을 few-shot으로 그대로 받아오는 유출 문제 발견, 17-4절) — 그래도 옵션 자체는
    # 남겨뒀으니(use_rag=True로 명시) mock 모드 end-to-end happy path가 깨지지 않는지 확인.
    # mock extract()는 RAG 로직 진입 전에 조기 반환하므로 영향 없어야 함.
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    graph = build_graph(use_rag=True)
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    draft = "내일까지 조금 더 고민해 보면 좋을 것 같아요"
    context = DraftContext(now_iso="2026-08-14T18:44:00+09:00")

    graph.invoke({"draft": draft, "context": context.model_dump()}, config=config)
    snapshot = graph.get_state(config)
    assert snapshot.interrupts
    assert snapshot.values["extraction"]["ambiguities"]
