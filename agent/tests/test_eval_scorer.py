from pathlib import Path

from ditto_agent.eval.golden import GoldenCase, load_golden_cases
from ditto_agent.eval.scorer import aggregate, score_case
from ditto_agent.schema import AmbiguityItem, ExtractionResult

GOLDEN_PATH = Path(__file__).resolve().parent.parent / "data" / "golden.json"


def _extraction(*categories: str) -> ExtractionResult:
    return ExtractionResult(
        task="t",
        request_type="r",
        decision_status="d",
        ambiguities=[
            AmbiguityItem(span="s", category=c, reason="r", candidates=["a"], suggestion="q") for c in categories
        ],
    )


def _case(expected: list[str]) -> GoldenCase:
    return GoldenCase(id="X", draft="d", expected_categories=frozenset(expected))


def test_exact_match_case_has_no_fn_or_fp():
    score = score_case(_case(["TIME"]), _extraction("TIME"))
    assert score.is_exact_match
    assert score.true_positive == {"TIME"}
    assert not score.false_negative and not score.false_positive


def test_missed_ambiguity_is_false_negative():
    score = score_case(_case(["TIME"]), _extraction())
    assert not score.is_exact_match
    assert score.false_negative == {"TIME"}


def test_unexpected_flag_on_control_case_is_false_positive():
    score = score_case(_case([]), _extraction("OTHER"))
    assert not score.is_exact_match
    assert score.false_positive == {"OTHER"}


def test_aggregate_overall_and_by_category():
    scores = [
        score_case(_case(["TIME"]), _extraction("TIME")),  # tp
        score_case(_case(["TIME"]), _extraction()),  # fn
        score_case(_case([]), _extraction("REQUEST_INTENT")),  # fp
    ]
    report = aggregate(scores)
    assert (report.overall.true_positive, report.overall.false_negative, report.overall.false_positive) == (1, 1, 1)
    assert report.overall.recall == 0.5
    assert report.by_category["TIME"].recall == 0.5
    assert report.by_category["REQUEST_INTENT"].precision == 0.0


def test_confusion_counts_recall_precision_none_when_no_denominator():
    report = aggregate([score_case(_case([]), _extraction())])
    assert report.overall.recall is None
    assert report.overall.precision is None


def test_golden_json_loads_and_pairs_expand_to_two_cases_each():
    cases = load_golden_cases(GOLDEN_PATH)
    ids = [c.id for c in cases]
    assert "T01-ambiguous" in ids and "T01-explicit" in ids
    assert len(cases) == len(set(ids))  # 모든 id가 유니크한지
    pair_cases = [c for c in cases if c.pair_id == "T01"]
    assert len(pair_cases) == 2
    ambiguous = next(c for c in pair_cases if c.id == "T01-ambiguous")
    explicit = next(c for c in pair_cases if c.id == "T01-explicit")
    assert ambiguous.expected_categories == {"TIME"}
    assert explicit.expected_categories == frozenset()
    # golden set 문구는 few-shot(culture_criteria.py)과 겹치면 안 됨 — prompt contamination 방지
    from ditto_agent.llm.culture_criteria import CULTURE_CRITERIA

    t01_phrase = next(r["phrase"] for r in CULTURE_CRITERIA if r["id"] == "T01")
    assert ambiguous.draft != t01_phrase
    assert explicit.draft != t01_phrase


def test_composite_case_expects_multiple_categories():
    cases = load_golden_cases(GOLDEN_PATH)
    composite = next(c for c in cases if c.id == "COMP-01")
    assert composite.expected_categories == {"TIME", "REQUEST_INTENT"}
    assert composite.pair_id is None
