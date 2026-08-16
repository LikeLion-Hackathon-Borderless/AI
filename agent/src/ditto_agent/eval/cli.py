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
        "--no-verify",
        action="store_true",
        help="extract() 1차 결과만 측정하고 verify() 2차 필터링을 생략 — reason-sync 등 verify"
        " 이전 실험과 비교할 때 씀. 기본은 verify 적용.",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="2026-08-16 세션에서 client.extract_batch()가 원인 불명으로 반복 무한 대기에"
        " 빠지는 걸 확인함(docs/progress.md) — 기본은 단건 extract()+verify() 순차 호출."
        " 이 플래그로 예전 배치 경로를 켤 수 있지만 불안정하다고 알려져 있음.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="--batch일 때만 씀 — 호출 한 번에 묶어 보낼 케이스 수. 응답에서 누락된 항목은 개별 호출로 폴백",
    )
    parser.add_argument(
        "--pace",
        type=float,
        default=float(os.getenv("DITTO_EVAL_PACE_SECONDS", "2.0")),
        help="live 모드에서 호출 사이 대기 시간(초) — 분당 요청 한도(TPM/RPM) 회피용",
    )
    return parser.parse_args(argv)


def _fetch_live_sequential(
    client: LLMClient, cases: list[GoldenCase], verify: bool, pace: float
) -> tuple[dict, bool]:
    # extract_batch()의 불안정성(위 --batch 도움말 참고) 때문에 기본 경로로 채택 — 케이스당
    # 호출 1~2개(verify 포함 시)라 느리지만, client.py의 timeout=60.0 덕분에 느린 호출도
    # 최악의 경우 60초 안에 실패하고 다음으로 넘어간다(오래 멈추는 대신 눈에 보이게 실패).
    results: dict[str, ExtractionResult] = {}
    aborted = False
    stage = "extract+verify" if verify else "extract"

    for case in cases:
        ctx = DraftContext(**case.context)
        try:
            r = client.extract(case.draft, ctx)
            if verify:
                r = r.model_copy(update={"ambiguities": client.verify(case.draft, r.ambiguities)})
            results[case.id] = r
            cache.save(case.draft, ctx, client.model, r, stage=stage)
            print(f"  {case.id}: ok", flush=True)
        except Exception as exc:  # noqa: BLE001 — 실패해도 이미 얻은 결과는 살리고 다음 케이스로
            print(f"  {case.id}: FAILED ({exc.__class__.__name__}) {str(exc)[:150]}", flush=True)
            if type(exc).__name__ == "RateLimitError":
                aborted = True
                break
        time.sleep(pace)

    return results, aborted


def _chunks(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _fetch_live_batch(client: LLMClient, cases: list[GoldenCase], batch_size: int, pace: float) -> tuple[dict, bool]:
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
    mode = os.getenv("DITTO_LLM_MODE", "live")  # LLMClient의 기본값과 반드시 일치시켜야 함(리포트 라벨용)

    cases = load_golden_cases(args.golden)
    if args.only:
        cases = [c for c in cases if args.only in c.id]
    if args.limit:
        cases = cases[: args.limit]

    client = LLMClient()
    verify = not args.no_verify
    stage = "extract+verify" if verify else "extract"
    results: dict[str, ExtractionResult] = {}
    to_call = cases

    if client.mode == "live" and not args.no_cache:
        to_call = []
        for case in cases:
            hit = cache.load(case.draft, DraftContext(**case.context), client.model, stage=stage)
            if hit is not None:
                results[case.id] = hit
            else:
                to_call.append(case)
        print(f"{len(results)}/{len(cases)} cached, {len(to_call)}개 실제 호출 필요")

    aborted = False
    if client.mode == "mock":
        for case in to_call:
            r = client.extract(case.draft, DraftContext(**case.context))
            if verify:
                r = r.model_copy(update={"ambiguities": client.verify(case.draft, r.ambiguities)})
            results[case.id] = r
    elif to_call:
        if args.batch:
            live_results, aborted = _fetch_live_batch(client, to_call, args.batch_size, args.pace)
        else:
            live_results, aborted = _fetch_live_sequential(client, to_call, verify, args.pace)
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
