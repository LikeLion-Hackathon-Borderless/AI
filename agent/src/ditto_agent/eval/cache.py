import hashlib
import inspect
import json
from pathlib import Path

from ditto_agent.llm import client as llm_client
from ditto_agent.llm import postfilter
from ditto_agent.llm.prompts import build_system_prompt
from ditto_agent.schema import DraftContext, ExtractionResult

DEFAULT_CACHE_DIR = Path(".eval_cache")


def _code_hash() -> str:
    # postfilter.py처럼 프롬프트가 아니라 순수 후처리 코드가 바뀌어도 결과가 달라지는데,
    # 프롬프트 해시만으로는 이걸 감지 못해서 캐시가 옛날(필터 적용 전) 응답을 계속
    # 재사용하는 버그가 있었다(2026-08-17 실측 — E1 적용 후에도 E0와 소수점까지 같은
    # precision이 나와서 발견). postfilter.py와 client.py(seed/temperature 등 샘플링
    # 설정 포함) 소스를 통째로 해시에 넣어, 이 파일들이 바뀌면 캐시도 같이 무효화되게 함.
    src = inspect.getsource(postfilter) + inspect.getsource(llm_client)
    return hashlib.sha256(src.encode("utf-8")).hexdigest()[:16]


def _cache_key(
    draft: str, context: DraftContext, model: str, stage: str = "extract", few_shot_ids: set[str] | None = None
) -> str:
    # 시스템 프롬프트(few-shot 포함)의 해시를 키에 넣어서, 프롬프트를 바꾸면(예: culture_criteria.py
    # 수정) 캐시가 자동으로 무효화되게 한다 — 안 그러면 옛날 프롬프트로 만든 응답을 새 프롬프트
    # 결과인 것처럼 계속 재사용하게 됨. stage("extract" vs "extract+verify")도 키에 넣어서
    # verify 유무가 다른 실험끼리 캐시를 잘못 공유하지 않게 함. code_hash는 위 _code_hash() 참고.
    # few_shot_ids(RAG로 draft마다 다르게 고른 few-shot 집합)도 build_system_prompt()에 그대로
    # 넘겨서 prompt_hash에 자연히 반영되게 함 — draft마다 다른 few-shot을 썼는데 캐시가 이걸
    # 못 감지하는 stale-cache 버그(postfilter.py 때 이미 한 번 겪음)가 RAG에서도 재발하지
    # 않도록.
    prompt_hash = hashlib.sha256(build_system_prompt(few_shot_ids=few_shot_ids).encode("utf-8")).hexdigest()[:16]
    payload = json.dumps(
        {
            "draft": draft,
            "context": context.model_dump(),
            "model": model,
            "prompt_hash": prompt_hash,
            "stage": stage,
            "code_hash": _code_hash(),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load(
    draft: str,
    context: DraftContext,
    model: str,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    stage: str = "extract",
    few_shot_ids: set[str] | None = None,
) -> ExtractionResult | None:
    path = cache_dir / f"{_cache_key(draft, context, model, stage, few_shot_ids)}.json"
    if not path.exists():
        return None
    return ExtractionResult.model_validate_json(path.read_text(encoding="utf-8"))


def save(
    draft: str,
    context: DraftContext,
    model: str,
    result: ExtractionResult,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    stage: str = "extract",
    few_shot_ids: set[str] | None = None,
) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{_cache_key(draft, context, model, stage, few_shot_ids)}.json"
    path.write_text(result.model_dump_json(), encoding="utf-8")
