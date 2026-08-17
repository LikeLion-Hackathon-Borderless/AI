from collections import defaultdict
from dataclasses import dataclass, field

from ditto_agent.eval.golden import GoldenCase
from ditto_agent.schema import AmbiguityCategory, ExtractionResult


@dataclass(frozen=True, slots=True)
class ConfusionCounts:
    true_positive: int = 0
    false_negative: int = 0
    false_positive: int = 0

    @property
    def recall(self) -> float | None:
        denom = self.true_positive + self.false_negative
        return self.true_positive / denom if denom else None

    @property
    def precision(self) -> float | None:
        denom = self.true_positive + self.false_positive
        return self.true_positive / denom if denom else None

    def __add__(self, other: "ConfusionCounts") -> "ConfusionCounts":
        return ConfusionCounts(
            true_positive=self.true_positive + other.true_positive,
            false_negative=self.false_negative + other.false_negative,
            false_positive=self.false_positive + other.false_positive,
        )


@dataclass(frozen=True, slots=True)
class CaseScore:
    case: GoldenCase
    got_categories: frozenset[AmbiguityCategory]
    true_positive: frozenset[AmbiguityCategory]
    false_negative: frozenset[AmbiguityCategory]
    false_positive: frozenset[AmbiguityCategory]

    @property
    def is_exact_match(self) -> bool:
        return not self.false_negative and not self.false_positive


def score_case(case: GoldenCase, result: ExtractionResult) -> CaseScore:
    got = frozenset(a.category for a in result.ambiguities)
    expected = case.expected_categories
    return CaseScore(
        case=case,
        got_categories=got,
        true_positive=expected & got,
        false_negative=expected - got,
        false_positive=got - expected,
    )


@dataclass(frozen=True, slots=True)
class AggregateReport:
    overall: ConfusionCounts
    by_category: dict[AmbiguityCategory, ConfusionCounts] = field(default_factory=dict)


def aggregate(scores: list[CaseScore]) -> AggregateReport:
    by_category: dict[AmbiguityCategory, ConfusionCounts] = defaultdict(ConfusionCounts)
    overall = ConfusionCounts()

    for score in scores:
        overall += ConfusionCounts(
            true_positive=len(score.true_positive),
            false_negative=len(score.false_negative),
            false_positive=len(score.false_positive),
        )
        # 카테고리별 집계 — 이 케이스가 관여한(기대했거나 실제로 나온) 카테고리에만 반영
        for category in score.case.expected_categories | score.got_categories:
            by_category[category] += ConfusionCounts(
                true_positive=1 if category in score.true_positive else 0,
                false_negative=1 if category in score.false_negative else 0,
                false_positive=1 if category in score.false_positive else 0,
            )

    return AggregateReport(overall=overall, by_category=dict(by_category))
