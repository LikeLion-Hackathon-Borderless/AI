import re

from ditto_agent.schema import AmbiguityItem

# 2026-08-17 세션에서 실측 확인된 과탐지 패턴 대응: "이번주 금요일 오후 5시(KST)까지"처럼
# 요일/날짜 + 시각(+시간대)이 전부 명시된 문장까지 TIME 모호성으로 잘못 플래그하는 경우가
# 있었다(golden set T02-explicit 등). API 호출 없이 코드로 바로 걸러낼 수 있는 명백한
# 케이스라 후처리 필터로 뺀다 — LLM 프롬프트를 더 건드리는 대신 결정적 규칙으로 처리.

# "내일"/"낼"은 시각이 같이 있어도 발신자/수신자 기준이 다를 수 있어(T01) 필터링 대상에서
# 제외 — 이 마커가 하나라도 있으면 아무리 명시적 시각이 있어도 필터링하지 않는다.
_VAGUE_TIME_MARKERS = ("내일", "낼", "곧", "빠른", "가능하면", "여유", "최대한", "일단", "이따가")

_CLOCK_PATTERN = re.compile(r"(오전|오후)?\s*\d{1,2}\s*시(?!간)|\d{1,2}:\d{2}")
_DATE_ANCHOR_PATTERN = re.compile(r"[월화수목금토일]요일|\d{1,2}월\s*\d{1,2}일|오늘")
_DURATION_PATTERN = re.compile(r"\d+\s*시간\s*(안에|이내)")


def _is_fully_explicit_time(draft: str) -> bool:
    if any(marker in draft for marker in _VAGUE_TIME_MARKERS):
        return False
    has_clock = bool(_CLOCK_PATTERN.search(draft))
    has_anchor = bool(_DATE_ANCHOR_PATTERN.search(draft))
    has_duration = bool(_DURATION_PATTERN.search(draft))
    return (has_clock and has_anchor) or has_duration


def filter_false_positive_time(draft: str, ambiguities: list[AmbiguityItem]) -> list[AmbiguityItem]:
    if not _is_fully_explicit_time(draft):
        return ambiguities
    return [a for a in ambiguities if a.category != "TIME"]
