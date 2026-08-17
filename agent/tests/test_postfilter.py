from ditto_agent.llm.postfilter import filter_false_positive_time
from ditto_agent.schema import AmbiguityItem

_TIME_ITEM = AmbiguityItem(span="s", category="TIME", reason="r", candidates=["c"], suggestion="s")
_OTHER_ITEM = AmbiguityItem(span="s", category="DECISION_STATUS", reason="r", candidates=["c"], suggestion="s")


def test_filters_time_item_when_weekday_and_clock_and_timezone_present():
    draft = "이거 이번주 금요일 오후 5시(KST)까지 부탁드려요"
    assert filter_false_positive_time(draft, [_TIME_ITEM]) == []


def test_filters_time_item_when_date_and_clock_present():
    draft = "8월 16일 18:00 KST까지 부탁드려도 될까요?"
    assert filter_false_positive_time(draft, [_TIME_ITEM]) == []


def test_filters_time_item_when_today_and_clock_present():
    draft = "이건 오늘이 필수 마감이라 꼭 오늘 오후 6시(KST)까지 봐주세요"
    assert filter_false_positive_time(draft, [_TIME_ITEM]) == []


def test_filters_time_item_when_explicit_duration_present():
    draft = "2시간 안에 다시 말씀드릴게요"
    assert filter_false_positive_time(draft, [_TIME_ITEM]) == []


def test_keeps_time_item_when_tomorrow_marker_present_even_with_clock():
    # "내일"은 발신자/수신자 시간대 기준이 여전히 다를 수 있어 명시적 시각이 있어도 유지
    draft = "내일 오후 6시까지 부탁드려요"
    assert filter_false_positive_time(draft, [_TIME_ITEM]) == [_TIME_ITEM]


def test_keeps_time_item_when_no_explicit_clock():
    draft = "이번 주 안에 부탁드립니다"
    assert filter_false_positive_time(draft, [_TIME_ITEM]) == [_TIME_ITEM]


def test_keeps_time_item_when_vague_marker_present_despite_day_mention():
    draft = "여유 되시면 오늘 안으로 봐주세요"
    assert filter_false_positive_time(draft, [_TIME_ITEM]) == [_TIME_ITEM]


def test_does_not_touch_non_time_categories():
    draft = "이번주 금요일 오후 5시(KST)까지 부탁드려요"
    assert filter_false_positive_time(draft, [_TIME_ITEM, _OTHER_ITEM]) == [_OTHER_ITEM]


def test_empty_ambiguities_stays_empty():
    assert filter_false_positive_time("아무 문장", []) == []
