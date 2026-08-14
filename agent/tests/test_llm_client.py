import os

from ditto_agent.llm.client import LLMClient
from ditto_agent.schema import DraftContext


def test_mock_extract_flags_time_and_intent_ambiguity(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    result = LLMClient().extract(
        "내일까지 조금 더 고민해 보면 좋을 것 같아요",
        DraftContext(now_iso="2026-08-14T18:44:00+09:00"),
    )
    categories = {a.category for a in result.ambiguities}
    assert categories == {"TIME", "REQUEST_INTENT"}


def test_mock_extract_suppresses_warnings_when_unambiguous(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    result = LLMClient().extract("8/20 18:00 KST까지 리뷰 부탁드립니다.", DraftContext())
    assert result.ambiguities == []


def test_mock_time_candidate_is_iso8601_and_one_day_ahead(monkeypatch):
    monkeypatch.setenv("DITTO_LLM_MODE", "mock")
    result = LLMClient().extract(
        "내일까지 부탁드려요",
        DraftContext(now_iso="2026-08-14T10:00:00+09:00"),
    )
    time_item = next(a for a in result.ambiguities if a.category == "TIME")
    assert time_item.candidates[0] == "2026-08-15T18:00:00+09:00"
