import hashlib
import json
from pathlib import Path

from ditto_agent.llm.prompts import build_system_prompt
from ditto_agent.schema import DraftContext, ExtractionResult

DEFAULT_CACHE_DIR = Path(".eval_cache")


def _cache_key(draft: str, context: DraftContext, model: str) -> str:
    # 시스템 프롬프트(few-shot 포함)의 해시를 키에 넣어서, 프롬프트를 바꾸면(예: culture_criteria.py
    # 수정) 캐시가 자동으로 무효화되게 한다 — 안 그러면 옛날 프롬프트로 만든 응답을 새 프롬프트
    # 결과인 것처럼 계속 재사용하게 됨.
    prompt_hash = hashlib.sha256(build_system_prompt().encode("utf-8")).hexdigest()[:16]
    payload = json.dumps(
        {"draft": draft, "context": context.model_dump(), "model": model, "prompt_hash": prompt_hash},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load(draft: str, context: DraftContext, model: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> ExtractionResult | None:
    path = cache_dir / f"{_cache_key(draft, context, model)}.json"
    if not path.exists():
        return None
    return ExtractionResult.model_validate_json(path.read_text(encoding="utf-8"))


def save(
    draft: str, context: DraftContext, model: str, result: ExtractionResult, cache_dir: Path = DEFAULT_CACHE_DIR
) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{_cache_key(draft, context, model)}.json"
    path.write_text(result.model_dump_json(), encoding="utf-8")
