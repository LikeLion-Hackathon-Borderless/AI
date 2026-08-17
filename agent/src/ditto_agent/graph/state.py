from typing import TypedDict


class GraphState(TypedDict, total=False):
    draft: str
    context: dict
    extraction: dict
    confirmed_ambiguities: list[dict]
    deadline_confirmed: str
    conflict: dict
    card: dict
