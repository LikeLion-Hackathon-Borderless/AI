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
