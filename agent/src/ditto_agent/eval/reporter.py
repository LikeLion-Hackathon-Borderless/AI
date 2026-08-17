import json
from pathlib import Path

from ditto_agent.eval.scorer import AggregateReport, CaseScore


def _pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.0%}"


def _confusion_row(label: str, counts) -> str:
    return f"| {label} | {counts.true_positive} | {counts.false_negative} | {counts.false_positive} | {_pct(counts.recall)} | {_pct(counts.precision)} |"


def _draft_snippet(draft: str, limit: int = 40) -> str:
    draft = draft.replace("\n", " ")
    return draft if len(draft) <= limit else draft[: limit - 1] + "…"


def render_markdown(scores: list[CaseScore], report: AggregateReport, mode: str) -> str:
    lines = ["# ditto-agent 골든셋 평가 결과", ""]
    if mode != "live":
        lines += [
            f"> ⚠️ `DITTO_LLM_MODE={mode}` — mock 추출기는 정확도용이 아닌 placeholder라",
            "> 이 리포트의 숫자는 하네스 동작 확인(smoke test)용일 뿐, 실제 정확도가 아닙니다.",
            "> `OPENAI_API_KEY` 세팅 후 `DITTO_LLM_MODE=live`로 다시 돌리세요.",
            "",
        ]

    lines += ["## 요약", "", "| 카테고리 | TP | FN | FP | Recall | Precision |", "|---|---|---|---|---|---|"]
    lines.append(_confusion_row("전체", report.overall))
    for category in sorted(report.by_category):
        lines.append(_confusion_row(category, report.by_category[category]))
    lines.append("")

    lines += ["## 케이스별 결과", "", "| ID | Pair | Draft | Expected | Got | 결과 |", "|---|---|---|---|---|---|"]
    for score in scores:
        verdict = "✅" if score.is_exact_match else "❌"
        expected = ", ".join(sorted(score.case.expected_categories)) or "(없음)"
        got = ", ".join(sorted(score.got_categories)) or "(없음)"
        lines.append(
            f"| {score.case.id} | {score.case.pair_id or '-'} | {_draft_snippet(score.case.draft)} "
            f"| {expected} | {got} | {verdict} |"
        )

    return "\n".join(lines) + "\n"


def render_json(scores: list[CaseScore], report: AggregateReport, mode: str) -> str:
    payload = {
        "mode": mode,
        "overall": {
            "true_positive": report.overall.true_positive,
            "false_negative": report.overall.false_negative,
            "false_positive": report.overall.false_positive,
            "recall": report.overall.recall,
            "precision": report.overall.precision,
        },
        "by_category": {
            category: {
                "true_positive": counts.true_positive,
                "false_negative": counts.false_negative,
                "false_positive": counts.false_positive,
                "recall": counts.recall,
                "precision": counts.precision,
            }
            for category, counts in report.by_category.items()
        },
        "cases": [
            {
                "id": score.case.id,
                "pair_id": score.case.pair_id,
                "draft": score.case.draft,
                "note": score.case.note,
                "expected_categories": sorted(score.case.expected_categories),
                "got_categories": sorted(score.got_categories),
                "exact_match": score.is_exact_match,
            }
            for score in scores
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def write_report(scores: list[CaseScore], report: AggregateReport, mode: str, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.md").write_text(render_markdown(scores, report, mode), encoding="utf-8")
    (out_dir / "report.json").write_text(render_json(scores, report, mode), encoding="utf-8")
