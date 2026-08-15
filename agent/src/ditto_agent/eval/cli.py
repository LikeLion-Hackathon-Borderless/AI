import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from ditto_agent.eval.golden import load_golden_cases
from ditto_agent.eval.reporter import write_report
from ditto_agent.eval.scorer import aggregate, score_case
from ditto_agent.llm.client import LLMClient
from ditto_agent.schema import DraftContext


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="ditto-eval")
    parser.add_argument("--golden", type=Path, default=Path("data/golden.json"))
    parser.add_argument("--out", type=Path, default=Path("outputs/eval"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    mode = os.getenv("DITTO_LLM_MODE", "mock")

    cases = load_golden_cases(args.golden)
    client = LLMClient()
    scores = [score_case(case, client.extract(case.draft, DraftContext(**case.context))) for case in cases]
    report = aggregate(scores)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_dir = args.out / timestamp
    write_report(scores, report, mode, out_dir)

    print(f"mode={mode} cases={len(cases)} recall={report.overall.recall} precision={report.overall.precision}")
    print(f"report written to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
