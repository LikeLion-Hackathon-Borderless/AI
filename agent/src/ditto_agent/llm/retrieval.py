import json
from collections.abc import Callable
from pathlib import Path

from ditto_agent.llm.culture_criteria import CULTURE_CRITERIA

DEFAULT_CACHE_PATH = Path(".criteria_embeddings.json")

# OTHER(C01-04)는 as_few_shot_examples()의 기존 관례와 동일하게 few-shot 후보에서 제외
_CANDIDATE_ROWS = [row for row in CULTURE_CRITERIA if row["category"] != "OTHER"]

EmbedFn = Callable[[str], list[float]]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def embed_criteria(embed_fn: EmbedFn, cache_path: Path = DEFAULT_CACHE_PATH) -> dict[str, list[float]]:
    # 후보 phrase 16개를 임베딩하는 건 draft마다 반복할 필요가 없는 고정 비용이라 디스크에
    # 캐시한다 — 프로세스 재시작마다(특히 eval처럼 케이스가 많을 때) 다시 임베딩하지 않게.
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass  # 캐시가 깨졌으면 새로 만든다 — 실패를 조용히 흡수

    embeddings = {row["id"]: embed_fn(row["phrase"]) for row in _CANDIDATE_ROWS}
    try:
        cache_path.write_text(json.dumps(embeddings), encoding="utf-8")
    except OSError:
        pass  # 캐시 저장 실패해도 이번 실행 결과엔 지장 없음 — 다음에 다시 씀
    return embeddings


def select_few_shot(
    embed_fn: EmbedFn,
    draft: str,
    k: int = 6,
    fallback: set[str] | None = None,
    cache_path: Path = DEFAULT_CACHE_PATH,
) -> set[str]:
    # draft와 코사인 유사도가 가장 높은 판단기준표 phrase id를 k개 고른다. RAG가 뭔가의
    # 이유로 실패해도(임베딩 API 에러, RPD, 차원이 안 맞는 캐시 등) 전체 파이프라인이
    # 죽으면 안 되므로 실패 시 고정 allowlist(prompts.FEW_SHOT_ALLOWLIST 등)로 폴백한다.
    # 코사인 계산(_cosine)까지 try 안에 넣어둔 이유: 캐시가 깨져서 차원이 안 맞는 벡터가
    # 섞여 있으면 embed_fn 호출 자체는 성공해도 sorted()에서 터질 수 있음(실제로 테스트가
    # 캐시 파일을 오염시켰다가 이 문제를 실측으로 잡음).
    try:
        criteria_embeddings = embed_criteria(embed_fn, cache_path=cache_path)
        draft_embedding = embed_fn(draft)
        scored = sorted(
            criteria_embeddings.items(),
            key=lambda kv: _cosine(draft_embedding, kv[1]),
            reverse=True,
        )
    except Exception:  # noqa: BLE001 — 임베딩/유사도 계산 실패는 RAG를 껐다고 보고 폴백하는 게 목적
        return fallback if fallback is not None else set()

    return {id_ for id_, _ in scored[:k]}
