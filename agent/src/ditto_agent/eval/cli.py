import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import UTC, datetime
from pathlib import Path

from ditto_agent.eval import cache
from ditto_agent.eval.golden import GoldenCase, load_golden_cases
from ditto_agent.eval.reporter import write_report
from ditto_agent.eval.scorer import aggregate, score_case
from ditto_agent.llm.client import LLMClient
from ditto_agent.llm.prompts import FEW_SHOT_ALLOWLIST
from ditto_agent.llm.retrieval import select_few_shot
from ditto_agent.schema import DraftContext, ExtractionResult


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="ditto-eval")
    parser.add_argument("--golden", type=Path, default=Path("data/golden.json"))
    parser.add_argument("--out", type=Path, default=Path("outputs/eval"))
    parser.add_argument("--limit", type=int, default=None, help="처음 N개 케이스만 실행 — 빠른 확인용")
    parser.add_argument("--only", type=str, default=None, help="이 문자열을 id에 포함하는 케이스만 실행 (예: T01)")
    parser.add_argument("--no-cache", action="store_true", help="live 모드에서도 캐시를 쓰지 않고 매번 새로 호출")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="extract() 뒤에 verify() 2차 필터링을 체이닝 — 기본은 생략(꺼짐). 2026-08-17"
        " gpt-5-mini 실측(docs/survey-results-analysis.md 10절)에서 verify가 precision을"
        " 오히려 악화시키는 게 확인돼(0.679→0.500) build_graph()의 프로덕션 기본값도 꺼짐으로"
        " 바뀜 — 이 플래그로 켜서 재측정/재튜닝할 때 씀.",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="여러 케이스를 한 호출로 묶어서(--batch-size) 요청 수(RPD) 자체를 아낀다 — RPD가"
        " 낮은 계정에서 권장. --verify와 같이 쓰면 배치당 extract+verify 2호출로 체이닝됨."
        " 개별 케이스가 배치 응답에서 누락되면 단건 호출로 자동 폴백.",
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
    parser.add_argument(
        "--consistency",
        type=int,
        default=0,
        help="0(기본, 꺼짐)보다 크면 케이스당 extract_consistent(n=이 값)로 self-consistency"
        " 다수결을 씀 — seed 고정만으로는 배치 구조화 출력의 실행 간 노이즈가 안 없어지는 게"
        " 실측으로 확인돼(survey-results-analysis.md 13절) 만든 구조적 대안. 케이스당 API 호출"
        " 수는 여전히 1번(배치 크기가 n일 뿐)이라 RPD 부담은 안 늘어남. --batch/--verify와는"
        " 같이 못 씀(둘 다 무시되고 이 경로가 우선).",
    )
    parser.add_argument(
        "--consistency-threshold",
        type=int,
        default=None,
        help="--consistency일 때만 씀 — 카테고리 채택에 필요한 최소 득표 수. 생략하면 만장일치(n) —"
        " 2026-08-17 실측(survey-results-analysis.md 13-1절)에서 과반(n//2+1)은 precision을"
        " 오히려 깎아먹었고(0.714) 만장일치는 recall/precision 둘 다 만점이 나옴.",
    )
    parser.add_argument(
        "--rag",
        action="store_true",
        help="draft마다 임베딩 유사도로 few-shot 6개를 동적 선택(llm/retrieval.py) — 기본 꺼짐,"
        " 아직 실측 전. --batch/--consistency와는 같이 못 씀(sequential 경로에서만 지원) —"
        " 임베딩 실패 시 고정 allowlist로 자동 폴백.",
    )
    return parser.parse_args(argv)


_HARD_TIMEOUT_SECONDS = 60.0


def _run_with_hard_timeout(fn, *args, timeout: float = _HARD_TIMEOUT_SECONDS):
    # client.py의 timeout=60.0(httpx read timeout)은 "마지막으로 뭔가 받은 시점부터"를 재는
    # idle timeout이라, 서버가 부하 상태에서 keep-alive 바이트만 간간이 흘려보내고 응답을 안
    # 끝내면 계속 갱신되기만 하고 절대 안 터진다(2026-08-17 세션에서 실측 — 단발 호출은 15초
    # 만에 깔끔히 timeout 났는데, 같은 설정으로 부하 누적된 상태의 실제 eval 루프는 50분+
    # 무한 대기). 스레드로 감싸서 "경과 시간이 얼마든 무조건 끊는" 하드 데드라인을 추가로 건다
    # — 워커 스레드가 안 끝나도 메인 루프는 넘어간다(스레드는 백그라운드에 버려짐, eval
    # 프로세스는 짧게 사는 CLI라 leak 걱정 없음).
    # `with ThreadPoolExecutor(...)`을 안 쓰는 이유: context manager의 __exit__은
    # shutdown(wait=True)를 호출해서 워커 스레드가 끝날 때까지 블록한다 — 그러면 스레드가
    # 안 끝났을 때 여기서 다시 무한정 멈추게 돼 하드 타임아웃의 의미가 없어진다. 대신
    # shutdown(wait=False)로 스레드를 안 기다리고 바로 버린다.
    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(fn, *args)
    try:
        return future.result(timeout=timeout)
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def _fetch_live_sequential(
    client: LLMClient,
    cases: list[GoldenCase],
    verify: bool,
    pace: float,
    few_shot_ids_by_case: dict[str, set[str] | None] | None = None,
) -> tuple[dict, bool]:
    # extract_batch()의 불안정성(위 --batch 도움말 참고) 때문에 기본 경로로 채택 — 케이스당
    # 호출 1~2개(verify 포함 시)라 느리지만, 각 호출을 _run_with_hard_timeout으로 감싸서
    # 어떤 이유로든 60초 넘게 멈추면 강제로 포기하고 다음 케이스로 넘어간다.
    # few_shot_ids_by_case가 주어지면(--rag) main()이 캐시 조회 때 이미 계산해둔 값을 그대로
    # 써서 임베딩 API를 중복 호출하지 않는다 — 캐시 키와 실제 호출이 항상 같은 few-shot
    # 선택을 쓰게 보장하는 목적도 있음(cache.py 참고).
    results: dict[str, ExtractionResult] = {}
    aborted = False
    stage = "extract+verify" if verify else "extract"

    for case in cases:
        ctx = DraftContext(**case.context)
        few_shot_ids = few_shot_ids_by_case.get(case.id) if few_shot_ids_by_case else None
        try:
            r = _run_with_hard_timeout(client.extract, case.draft, ctx, few_shot_ids)
            if verify:
                verified = _run_with_hard_timeout(client.verify, case.draft, r.ambiguities)
                r = r.model_copy(update={"ambiguities": verified})
            results[case.id] = r
            cache.save(case.draft, ctx, client.model, r, stage=stage, few_shot_ids=few_shot_ids)
            print(f"  {case.id}: ok", flush=True)
        except FutureTimeoutError:
            print(f"  {case.id}: FAILED (하드 타임아웃 {_HARD_TIMEOUT_SECONDS}초 초과, 스레드 방치하고 다음으로)", flush=True)
        except Exception as exc:  # noqa: BLE001 — 실패해도 이미 얻은 결과는 살리고 다음 케이스로
            print(f"  {case.id}: FAILED ({exc.__class__.__name__}) {str(exc)[:150]}", flush=True)
            if type(exc).__name__ == "RateLimitError":
                aborted = True
                break
        time.sleep(pace)

    return results, aborted


def _fetch_live_consistency(
    client: LLMClient,
    cases: list[GoldenCase],
    n: int,
    threshold: int,
    pace: float,
    few_shot_ids_by_case: dict[str, set[str] | None] | None = None,
) -> tuple[dict, bool]:
    # _fetch_live_sequential()과 같은 케이스별 순회 구조지만 client.extract_batch() 대신
    # client.extract_consistent()를 호출 — 케이스 하나당 API 요청은 여전히 1개(배치 크기 n)라
    # RPD 부담이 늘지 않으면서 실행 간 다수결로 노이즈를 줄인다.
    # few_shot_ids_by_case가 주어지면(--rag --consistency 같이 씀) main()이 미리 계산해둔
    # 값을 그대로 씀 — extract_consistent() 안에서 배치 n개 항목이 전부 같은 draft라 few-shot도
    # 하나만 계산하면 됨(extract_batch()의 few_shot_ids 파라미터 참고).
    results: dict[str, ExtractionResult] = {}
    aborted = False
    stage = f"extract-consistency-n{n}-t{threshold}"
    if few_shot_ids_by_case:
        stage += "-rag"

    for case in cases:
        ctx = DraftContext(**case.context)
        few_shot_ids = few_shot_ids_by_case.get(case.id) if few_shot_ids_by_case else None
        try:
            r = _run_with_hard_timeout(client.extract_consistent, case.draft, ctx, n, threshold, few_shot_ids)
            results[case.id] = r
            cache.save(case.draft, ctx, client.model, r, stage=stage, few_shot_ids=few_shot_ids)
            print(f"  {case.id}: ok", flush=True)
        except FutureTimeoutError:
            print(f"  {case.id}: FAILED (하드 타임아웃 {_HARD_TIMEOUT_SECONDS}초 초과, 스레드 방치하고 다음으로)", flush=True)
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


def _fetch_live_batch(
    client: LLMClient, cases: list[GoldenCase], batch_size: int, pace: float, verify: bool = False
) -> tuple[dict, bool]:
    # verify=True면 배치 하나(extract) 끝날 때마다 그 배치 그대로 verify_batch()도 한 번 더
    # 불러서 체이닝한다 — 케이스 수와 무관하게 배치당 요청 2개(extract+verify)로 고정되니
    # RPD 절약 효과가 verify 없을 때와 동일한 비율로 유지된다.
    results: dict[str, ExtractionResult] = {}
    aborted = False
    stage = "extract+verify" if verify else "extract"

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

        batch_extractions: dict[str, ExtractionResult] = {}
        for i, case in enumerate(batch):
            if i in batch_results:
                batch_extractions[case.id] = batch_results[i]
            else:
                print(f"  {case.id}: 배치 응답에 없음 — 개별 재시도 ...", end=" ", flush=True)
                try:
                    batch_extractions[case.id] = client.extract(case.draft, DraftContext(**case.context))
                    print("ok")
                except Exception as exc2:  # noqa: BLE001
                    print(f"FAILED ({exc2.__class__.__name__})")
                    if type(exc2).__name__ == "RateLimitError":
                        aborted = True

        if verify and not aborted and batch_extractions:
            verify_items = [(case.draft, batch_extractions[case.id].ambiguities) for case in batch if case.id in batch_extractions]
            verify_case_ids = [case.id for case in batch if case.id in batch_extractions]
            try:
                verified = client.verify_batch(verify_items)
                for i, case_id in enumerate(verify_case_ids):
                    if i in verified:
                        batch_extractions[case_id] = batch_extractions[case_id].model_copy(
                            update={"ambiguities": verified[i]}
                        )
            except Exception as exc:  # noqa: BLE001 — verify 실패해도 1차 extract 결과는 살린다
                print(f"  verify_batch FAILED ({exc.__class__.__name__}): {str(exc)[:200]}")
                if type(exc).__name__ == "RateLimitError":
                    aborted = True

        for case_id, extraction in batch_extractions.items():
            print(f"  {case_id}: ok")
            results[case_id] = extraction
            case = next(c for c in batch if c.id == case_id)
            cache.save(case.draft, DraftContext(**case.context), client.model, extraction, stage=stage)

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

    consistency_n = args.consistency
    # --rag + --consistency는 같이 쓸 수 있음 — extract_consistent()의 배치 n개 항목이 전부
    # 같은 draft라 few-shot도 하나만 계산하면 되기 때문(extract_batch()의 일반 eval-batch
    # 케이스처럼 서로 다른 draft가 한 system prompt를 공유하는 문제가 없음). --batch(서로
    # 다른 케이스를 한 요청에 묶음)만 여전히 지원 안 함.
    use_rag = args.rag and not args.batch
    if args.rag and not use_rag:
        print("--rag는 --batch와 같이 못 써서 무시됩니다 (sequential/consistency 경로 전용)")

    client = LLMClient(use_rag=use_rag)
    verify = args.verify
    consistency_threshold = args.consistency_threshold or consistency_n
    stage = f"extract-consistency-n{consistency_n}-t{consistency_threshold}" if consistency_n else (
        "extract+verify" if verify else "extract"
    )
    if use_rag:
        stage += "-rag"

    # RAG일 때 few-shot 선택을 여기서 한 번만 계산해서 캐시 조회·실제 호출 양쪽에 그대로
    # 씀 — 임베딩 API를 두 번 부르지 않기 위함(cache.py의 few_shot_ids 파라미터 참고).
    few_shot_ids_by_case: dict[str, set[str] | None] = {}
    if use_rag:
        for case in cases:
            few_shot_ids_by_case[case.id] = select_few_shot(
                client.embed, case.draft, k=6, fallback=FEW_SHOT_ALLOWLIST
            )

    results: dict[str, ExtractionResult] = {}
    to_call = cases

    if client.mode == "live" and not args.no_cache:
        to_call = []
        for case in cases:
            few_shot_ids = few_shot_ids_by_case.get(case.id)
            hit = cache.load(
                case.draft, DraftContext(**case.context), client.model, stage=stage, few_shot_ids=few_shot_ids
            )
            if hit is not None:
                results[case.id] = hit
            else:
                to_call.append(case)
        print(f"{len(results)}/{len(cases)} cached, {len(to_call)}개 실제 호출 필요")

    aborted = False
    if client.mode == "mock":
        for case in to_call:
            if consistency_n:
                r = client.extract_consistent(case.draft, DraftContext(**case.context), consistency_n, consistency_threshold)
            else:
                r = client.extract(case.draft, DraftContext(**case.context))
                if verify:
                    r = r.model_copy(update={"ambiguities": client.verify(case.draft, r.ambiguities)})
            results[case.id] = r
    elif to_call:
        if consistency_n:
            live_results, aborted = _fetch_live_consistency(
                client, to_call, consistency_n, consistency_threshold, args.pace,
                few_shot_ids_by_case if use_rag else None,
            )
        elif args.batch:
            live_results, aborted = _fetch_live_batch(client, to_call, args.batch_size, args.pace, verify)
        else:
            live_results, aborted = _fetch_live_sequential(
                client, to_call, verify, args.pace, few_shot_ids_by_case if use_rag else None
            )
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
