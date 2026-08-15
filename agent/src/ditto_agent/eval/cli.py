import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from ditto_agent.eval import cache
from ditto_agent.eval.golden import load_golden_cases
from ditto_agent.eval.reporter import write_report
from ditto_agent.eval.scorer import aggregate, score_case
from ditto_agent.llm.client import LLMClient
from ditto_agent.schema import DraftContext


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="ditto-eval")
    parser.add_argument("--golden", type=Path, default=Path("data/golden.json"))
    parser.add_argument("--out", type=Path, default=Path("outputs/eval"))
    parser.add_argument("--limit", type=int, default=None, help="처음 N개 케이스만 실행 — 빠른 확인용")
    parser.add_argument("--only", type=str, default=None, help="이 문자열을 id에 포함하는 케이스만 실행 (예: T01)")
    parser.add_argument("--no-cache", action="store_true", help="live 모드에서도 캐시를 쓰지 않고 매번 새로 호출")
    return parser.parse_args(argv)


def _extract_cached(client: LLMClient, case_draft: str, context: DraftContext, use_cache: bool):
    if client.mode != "live" or not use_cache:
        return client.extract(case_draft, context), False

    hit = cache.load(case_draft, context, client.model)
    if hit is not None:
        return hit, True
    result = client.extract(case_draft, context)
    cache.save(case_draft, context, client.model, result)
    return result, False


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    mode = os.getenv("DITTO_LLM_MODE", "mock")

    cases = load_golden_cases(args.golden)
    if args.only:
        cases = [c for c in cases if args.only in c.id]
    if args.limit:
        cases = cases[: args.limit]

    client = LLMClient()
    scores = []
    aborted = False
    for i, case in enumerate(cases, start=1):
        print(f"[{i}/{len(cases)}] {case.id} ...", end=" ", flush=True)
        try:
            result, from_cache = _extract_cached(client, case.draft, DraftContext(**case.context), not args.no_cache)
        except Exception as exc:  # noqa: BLE001 — golden-set 실행 중 하나가 실패해도 나머지/이미 번 호출은 살린다
            is_rate_limit = type(exc).__name__ == "RateLimitError"
            print(f"FAILED ({exc.__class__.__name__})")
            if is_rate_limit:
                print("rate limit — 남은 케이스 건너뛰고 지금까지 결과로 리포트를 씁니다.")
                aborted = True
                break
            print("  이 케이스만 건너뜁니다.")
            continue

        score = score_case(case, result)
        tag = " [cache]" if from_cache else ""
        print(("ok" if score.is_exact_match else f"mismatch (got={sorted(score.got_categories)})") + tag, flush=True)
        scores.append(score)

    report = aggregate(scores)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_dir = args.out / timestamp
    write_report(scores, report, mode, out_dir)

    status = "partial (rate limit)" if aborted else "complete"
    print(f"mode={mode} status={status} cases={len(scores)}/{len(cases)} "
          f"recall={report.overall.recall} precision={report.overall.precision}")
    print(f"report written to {out_dir}")
    return 1 if aborted else 0


if __name__ == "__main__":
    raise SystemExit(main())
