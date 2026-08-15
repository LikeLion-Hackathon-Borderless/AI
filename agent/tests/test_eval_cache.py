from ditto_agent.eval import cache
from ditto_agent.schema import DraftContext, ExtractionResult

_RESULT = ExtractionResult(task="t", request_type="r", decision_status="d", ambiguities=[])


def test_cache_roundtrip(tmp_path):
    ctx = DraftContext(now_iso="2026-08-15T10:00:00+09:00")
    assert cache.load("draft", ctx, "gpt-5", cache_dir=tmp_path) is None

    cache.save("draft", ctx, "gpt-5", _RESULT, cache_dir=tmp_path)
    hit = cache.load("draft", ctx, "gpt-5", cache_dir=tmp_path)
    assert hit == _RESULT


def test_cache_key_differs_by_draft_context_and_model(tmp_path):
    ctx1 = DraftContext(now_iso="2026-08-15T10:00:00+09:00")
    ctx2 = DraftContext(now_iso="2026-08-16T10:00:00+09:00")
    cache.save("draft-A", ctx1, "gpt-5", _RESULT, cache_dir=tmp_path)

    assert cache.load("draft-B", ctx1, "gpt-5", cache_dir=tmp_path) is None  # 다른 draft
    assert cache.load("draft-A", ctx2, "gpt-5", cache_dir=tmp_path) is None  # 다른 context
    assert cache.load("draft-A", ctx1, "gpt-4o", cache_dir=tmp_path) is None  # 다른 model


def test_cache_invalidated_when_system_prompt_changes(tmp_path, monkeypatch):
    ctx = DraftContext(now_iso="2026-08-15T10:00:00+09:00")
    cache.save("draft", ctx, "gpt-5", _RESULT, cache_dir=tmp_path)
    assert cache.load("draft", ctx, "gpt-5", cache_dir=tmp_path) == _RESULT

    # prompts.py가 바뀌면(예: culture_criteria.py 수정) 옛 캐시가 자동으로 무효화돼야 함
    monkeypatch.setattr("ditto_agent.eval.cache.build_system_prompt", lambda: "완전히 다른 프롬프트")
    assert cache.load("draft", ctx, "gpt-5", cache_dir=tmp_path) is None
