import argparse
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from ditto_agent.eval import cache
from ditto_agent.eval.golden import GoldenCase, load_golden_cases
from ditto_agent.eval.reporter import write_report
from ditto_agent.eval.scorer import aggregate, score_case
from ditto_agent.llm.client import LLMClient
from ditto_agent.schema import DraftContext, ExtractionResult


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="ditto-eval")
    parser.add_argument("--golden", type=Path, default=Path("data/golden.json"))
    parser.add_argument("--out", type=Path, default=Path("outputs/eval"))
    parser.add_argument("--limit", type=int, default=None, help="처음 N개 케이스만 실행 — 빠른 확인용")
    parser.add_argument("--only", type=str, default=None, help="이 문자열을 id에 포함하는 케이스만 실행 (예: T01)")
    parser.add_argument("--no-cache", action="store_true", help="live 모드에서도 캐시를 쓰지 않고 매번 새로 호출")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="live 모드에서 호출 한 번에 묶어 보낼 케이스 수 — 요청 수(RPD) 자체가 쿼터인 계정에서는"
        " 이걸 늘리면 호출 횟수가 줄어든다. 응답에서 누락된 항목은 개별 호출로 폴백",
    )
    parser.add_argument(
        "--pace",
        type=float,
        default=float(os.getenv("DITTO_EVAL_PACE_SECONDS", "2.0")),
        help="live 모드에서 배치 호출 사이 대기 시간(초) — 분당 요청 한도(RPM) 회피용",
    )
    return parser.parse_args(argv)


def _chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _fetch_live(client: LLMClient, cases: list[GoldenCase], batch_size: int, pace: float) -> tuple[dict, bool]:
    results: dict[str, ExtractionResult] = {}
    aborted = False

    for batch in _chunks(cases, batch_size):
        print(f"batch({len(batch)}): {', '.join(c.id for c in batch)} ...", flush=True)
        items = [(c.draft, DraftContext(**c.context)) for c in batch]
        try:
            batch_results = client.extract_batch(items)
        except Exception as exc:  # noqa: BLE001 — 배치 전체가 죽어도 이미 얻은 결과는 살린다
            print(f"  배치 FAILED ({exc.__class__.__name__}): {str(exc)[:200]}")
            if type(exc).__name__ == "RateLimitError":
                aborted = True
                break
            batch_results = {}

        for i, case in enumerate(batch):
            if i in batch_results:
                print(f"  {case.id}: ok")
                results[case.id] = batch_results[i]
                cache.save(case.draft, DraftContext(**case.context), client.model, batch_results[i])
            else:
                print(f"  {case.id}: 배치 응답에 없음 — 개별 재시도 ...", end=" ", flush=True)
                try:
                    r = client.extract(case.draft, DraftContext(**case.context))
                    results[case.id] = r
                    cache.save(case.draft, DraftContext(**case.context), client.model, r)
                    print("ok")
                except Exception as exc2:  # noqa: BLE001
                    print(f"FAILED ({exc2.__class__.__name__})")
                    if type(exc2).__name__ == "RateLimitError":
                        aborted = True

        if aborted:
            break
        time.sleep(pace)

    return results, aborted


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    mode = os.getenv("DITTO_LLM_MODE", "mock")

    cases = load_golden_cases(args.golden)
    if args.only:
        cases = [c for c in cases if args.only in c.id]
    if args.limit:
        cases = cases[: args.limit]

    client = LLMClient()
    results: dict[str, ExtractionResult] = {}
    to_call = cases

    if client.mode == "live" and not args.no_cache:
        to_call = []
        for case in cases:
            hit = cache.load(case.draft, DraftContext(**case.context), client.model)
            if hit is not None:
                results[case.id] = hit
            else:
                to_call.append(case)
        print(f"{len(results)}/{len(cases)} cached, {len(to_call)}개 실제 호출 필요")

    aborted = False
    if client.mode == "mock":
        for case in to_call:
            results[case.id] = client.extract(case.draft, DraftContext(**case.context))
    elif to_call:
        live_results, aborted = _fetch_live(client, to_call, args.batch_size, args.pace)
        results.update(live_results)

    scores = []
    for case in cases:
        if case.id not in results:
            continue
        score = score_case(case, results[case.id])
        print(f"[{case.id}] " + ("ok" if score.is_exact_match else f"mismatch (got={sorted(score.got_categories)})"))
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
