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

    # cache_path를 tmp_path로 지정 — 안 그러면 기본 캐시 경로(레포 루트의 진짜
    # .criteria_embeddings.json)에 이 테스트의 가짜 2차원 벡터가 저장돼서, 실제 라이브
    # 실행이 그 캐시를 읽다가 진짜 임베딩(1536차원)과 차원이 안 맞아 깨지는 사고가 실제로
    # 났었다(2026-08-17).
    result = retrieval.select_few_shot(fn, "query", k=1, fallback=set(), cache_path=tmp_path / "criteria.json")
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


def test_select_few_shot_falls_back_on_dimension_mismatch(tmp_path, monkeypatch):
    # 회귀 테스트 — 캐시에 저장된 벡터 차원과 실제 embed_fn이 주는 draft 벡터 차원이
    # 다르면(예: 캐시는 옛날 2차원 테스트 데이터, 실제는 1536차원 진짜 임베딩) sorted()
    # 안의 코사인 계산이 통째로 죽는데, RAG 하나 때문에 전체 eval 실행이 멎으면 안 되므로
    # 폴백해야 한다. 2026-08-17에 테스트가 캐시를 오염시켜 실제로 이 사고가 남 — 이후
    # cache_path 격리(위 테스트 수정)와 이 폴백 둘 다로 방어.
    cache_path = tmp_path / "criteria.json"
    monkeypatch.setattr(retrieval, "_CANDIDATE_ROWS", [{"id": "A", "phrase": "x"}])
    retrieval.embed_criteria(lambda text: [1.0, 0.0], cache_path=cache_path)  # 2차원으로 캐시 생성

    def three_dim_embed(text: str) -> list[float]:
        return [1.0, 0.0, 0.0]  # 캐시(2차원)와 차원이 다름

    result = retrieval.select_few_shot(three_dim_embed, "query", fallback={"FALLBACK"}, cache_path=cache_path)
    assert result == {"FALLBACK"}
