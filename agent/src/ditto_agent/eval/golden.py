import json
from dataclasses import dataclass, field
from pathlib import Path

from ditto_agent.schema import AmbiguityCategory


@dataclass(frozen=True, slots=True)
class GoldenCase:
    id: str
    draft: str
    expected_categories: frozenset[AmbiguityCategory]
    pair_id: str | None = None
    context: dict = field(default_factory=dict)
    note: str = ""


def load_golden_cases(path: Path) -> list[GoldenCase]:
    # 매번 새로 읽는다 — golden.json이 하드코딩돼 캐시되는 일이 없도록 (planqa golden.py 관례)
    data = json.loads(path.read_text(encoding="utf-8"))
    default_context = data.get("default_context", {})
    cases: list[GoldenCase] = []

    for pair in data.get("pairs", []):
        pair_id = pair["pair_id"]
        for variant in ("ambiguous", "explicit"):
            entry = pair[variant]
            cases.append(
                GoldenCase(
                    id=f"{pair_id}-{variant}",
                    draft=entry["draft"],
                    expected_categories=frozenset(entry["expected_categories"]),
                    pair_id=pair_id,
                    context={**default_context, **entry.get("context", {})},
                    note=pair.get("note", ""),
                )
            )

    for composite in data.get("composites", []):
        cases.append(
            GoldenCase(
                id=composite["id"],
                draft=composite["draft"],
                expected_categories=frozenset(composite["expected_categories"]),
                pair_id=None,
                context={**default_context, **composite.get("context", {})},
                note=composite.get("note", ""),
            )
        )

    return cases
