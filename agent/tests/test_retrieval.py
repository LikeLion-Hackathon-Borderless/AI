from ditto_agent.llm import retrieval


def _fake_embed(vectors: dict[str, list[float]]):
    # 텍스트 -> 미리 정해둔 벡터를 돌려주는 가짜 embed_fn. retrieval.py는 phrase 텍스트로
    # 임베딩을 요청하므로, 테스트에서는 phrase 자체를 키로 벡터를 미리 심어둔다.
    def fn(text: str) -> list[float]:
        return vectors[text]

    return fn


def test_cosine_identical_vectors_is_one():
    assert retrieval._cosine([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_cosine_orthogonal_vectors_is_zero():
    assert retrieval._cosine([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_cosine_handles_zero_vector_without_dividing_by_zero():
    assert retrieval._cosine([0.0, 0.0], [1.0, 0.0]) == 0.0


def test_embed_criteria_caches_to_disk(tmp_path):
    cache_path = tmp_path / "criteria.json"
    calls = []

    def fn(text: str) -> list[float]:
        calls.append(text)
        return [1.0, 0.0]

    first = retrieval.embed_criteria(fn, cache_path=cache_path)
    assert cache_path.exists()
    n_calls_first_run = len(calls)

    second = retrieval.embed_criteria(fn, cache_path=cache_path)
    assert second == first
    assert len(calls) == n_calls_first_run  # 캐시 히트라 embed_fn을 다시 안 부름


def test_embed_criteria_recovers_from_corrupt_cache(tmp_path):
    cache_path = tmp_path / "criteria.json"
    cache_path.write_text("not valid json", encoding="utf-8")

    result = retrieval.embed_criteria(lambda text: [1.0, 0.0], cache_path=cache_path)
    assert result  # 깨진 캐시를 무시하고 새로 만듦


def test_select_few_shot_picks_closest_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(
        retrieval,
        "_CANDIDATE_ROWS",
        [
            {"id": "A", "phrase": "close"},
            {"id": "B", "phrase": "far"},
        ],
    )
    vectors = {"close": [1.0, 0.0], "far": [0.0, 1.0], "query": [0.9, 0.1]}
    fn = _fake_embed(vectors)

    result = retrieval.select_few_shot(fn, "query", k=1, fallback=set())
    assert result == {"A"}


def test_select_few_shot_falls_back_on_embedding_failure():
    def failing_embed(text: str) -> list[float]:
        raise RuntimeError("embedding API down")

    result = retrieval.select_few_shot(failing_embed, "아무 draft", fallback={"T01", "F01"})
    assert result == {"T01", "F01"}


def test_select_few_shot_falls_back_to_empty_set_without_explicit_fallback():
    def failing_embed(text: str) -> list[float]:
        raise RuntimeError("embedding API down")

    result = retrieval.select_few_shot(failing_embed, "아무 draft")
    assert result == set()
