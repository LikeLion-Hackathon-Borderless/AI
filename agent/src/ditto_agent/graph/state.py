from typing import TypedDict


class GraphState(TypedDict, total=False):
    draft: str
    context: dict
    extraction: dict
    time_confirmed: str
    interp_confirmed: str
    conflict: dict
    card: dict
