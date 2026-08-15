# 구조화된 형태의 docs/문화_판단기준표_초안.md — 손으로 동기화 유지, verified=False는
# 아직 인터뷰 검증 전이라는 뜻(검증 계획은 그 문서 참고).
from typing import Literal, TypedDict

Category = Literal["TIME", "REQUEST_INTENT", "DECISION_STATUS", "OTHER"]


class CriteriaRow(TypedDict):
    id: str
    category: Category
    direction: str  # "양방향" | "KR→US" | "US→KR"
    phrase: str
    reason: str
    candidates: list[str]
    suggestion: str
    verified: bool


CULTURE_CRITERIA: list[CriteriaRow] = [
    {
        "id": "T01",
        "category": "TIME",
        "direction": "양방향",
        "phrase": "내일까지 부탁드려요",
        "reason": "발신자/수신자 시간대 기준 불명확",
        "candidates": ["발신자 근무일 종료 시각(예: 7/30 18:00 KST) 기준", "수신자 근무일 종료 시각 기준"],
        "suggestion": "'내일까지'는 정확히 몇 시(어느 시간대) 기준인가요?",
        "verified": False,
    },
    {
        "id": "T02",
        "category": "TIME",
        "direction": "양방향",
        "phrase": "빠른 시일 내로",
        "reason": "상대적 표현, 구체적 기한 없음",
        "candidates": ["1~2일 내", "이번 주 내", "구체적 날짜 지정 필요"],
        "suggestion": "'빠른 시일 내로'의 구체적 기한이 필요합니다. 예: 이번주 금요일 오후 5시까지",
        "verified": False,
    },
    {
        "id": "T03",
        "category": "TIME",
        "direction": "양방향",
        "phrase": "가능하면 오늘 중으로",
        "reason": "'가능하면'이 우선순위를 낮추는지 실제 마감인지 모호",
        "candidates": ["오늘 필수 마감", "오늘이 이상적이나 늦어도 내일 정오까지 가능"],
        "suggestion": "이건 오늘 반드시 필요한 요청인가요, 여유가 있는 요청인가요?",
        "verified": False,
    },
    {
        "id": "T04",
        "category": "TIME",
        "direction": "양방향",
        "phrase": "이번 주 중으로",
        "reason": "요일 범위가 넓어 실제 작업 착수 시점 예측 어려움",
        "candidates": ["수요일까지 초안, 금요일까지 최종본", "금요일 하루가 마감"],
        "suggestion": "'이번 주 중으로'를 요일 단위로 나눠 확정해 주시겠어요?",
        "verified": False,
    },
    {
        "id": "T05",
        "category": "TIME",
        "direction": "양방향",
        "phrase": "곧 다시 연락드릴게요",
        "reason": "'곧'의 기준(시간 단위)이 문화/개인마다 상이",
        "candidates": ["2시간 내로 회신", "내일 오전까지 회신"],
        "suggestion": "'곧'이 대략 몇 시간/언제를 의미하나요?",
        "verified": False,
    },
    {
        "id": "F01",
        "category": "REQUEST_INTENT",
        "direction": "KR→US",
        "phrase": "이 방향도 좋은데 조금 더 고민해보면 어떨까요",
        "reason": "발신자 의도(현재 안 재검토 요청 · 완곡한 반대)와 수신자 해석(긍정 평가 + 선택적 제안) 사이 간극",
        "candidates": ["현재 방향 유지 + 세부 보완", "완곡한 반대 · 재검토 요청"],
        "suggestion": "실제 의도가 재검토 요청인지, 현재 방향을 유지한 보완 요청인지 확정해주세요.",
        "verified": False,
    },
    {
        "id": "F02",
        "category": "REQUEST_INTENT",
        "direction": "KR→US",
        "phrase": "다들 그렇게 생각하시는 것 같아요",
        "reason": "팀 차원의 우려 전달인지, 근거 없는 동조 압박으로 읽힐지 모호",
        "candidates": ["구체적 인원·근거를 명시한 우려 전달", "화자 개인 의견을 팀 의견으로 일반화"],
        "suggestion": "'다들'이 구체적으로 누구의 의견인가요? 근거를 명시해주시겠어요?",
        "verified": False,
    },
    {
        "id": "F03",
        "category": "REQUEST_INTENT",
        "direction": "KR→US",
        "phrase": "괜찮은 것 같아요, 근데...",
        "reason": "'근데' 이후가 핵심 피드백인데 '괜찮다'는 승인으로 읽혀 경시될 수 있음",
        "candidates": ["전체 승인 + 사소한 참고 코멘트", "부분 승인 + 필수 수정 요청"],
        "suggestion": "승인 여부와 수정 요청을 분리해서 명확히 해주시겠어요?",
        "verified": False,
    },
    {
        "id": "F04",
        "category": "REQUEST_INTENT",
        "direction": "US→KR",
        "phrase": "This is great, but I think we should reconsider X",
        "reason": "발신자는 구체적 수정을 요구하지만, 수신자는 전체 승인 후 사소한 코멘트로 축소 해석할 수 있음",
        "candidates": ["전체 승인 + 참고 의견", "X에 대한 필수 수정 요청"],
        "suggestion": "X에 대한 재고가 필수 수정사항인가요, 참고용 의견인가요?",
        "verified": False,
    },
    {
        "id": "F05",
        "category": "REQUEST_INTENT",
        "direction": "US→KR",
        "phrase": "I strongly disagree with this approach",
        "reason": "업무적 반대 표현이 개인적 감정 신호나 관계 악화로 오해될 수 있음",
        "candidates": ["업무적 반대(관계와 무관)", "강한 불만 · 관계 이슈로 인식될 위험"],
        "suggestion": "반대 근거와 대안을 함께 제시해 업무적 반대임을 명확히 하시겠어요?",
        "verified": False,
    },
    {
        "id": "F06",
        "category": "REQUEST_INTENT",
        "direction": "US→KR",
        "phrase": "Can you walk me through your reasoning?",
        "reason": "이해를 위한 질문인지, 결정에 대한 추궁으로 읽힐지 모호",
        "candidates": ["이해를 돕기 위한 질문", "결정에 대한 불신 · 재검토 요구로 해석될 위험"],
        "suggestion": "이 질문의 목적이 이해를 위한 것임을 먼저 밝히시겠어요?",
        "verified": False,
    },
    {
        "id": "D01",
        "category": "DECISION_STATUS",
        "direction": "양방향",
        "phrase": "일단 이렇게 진행해봐요",
        "reason": "최종 승인인지 임시 시도인지 불명확",
        "candidates": ["이 안으로 최종 확정", "1차 테스트로 진행, 결과 보고 재결정"],
        "suggestion": "이건 최종 확정인가요, 임시 시도인가요?",
        "verified": False,
    },
    {
        "id": "D02",
        "category": "DECISION_STATUS",
        "direction": "양방향",
        "phrase": "Review complete",
        "reason": "조직마다 '완료'의 의미가 다름(최종 승인 vs 1차 검토)",
        "candidates": ["최종 승인 완료", "1차 검토만 완료, 추가 승인 필요"],
        "suggestion": "'완료'가 최종 승인을 의미하나요, 1차 검토만 마쳤다는 뜻인가요?",
        "verified": False,
    },
    {
        "id": "D03",
        "category": "DECISION_STATUS",
        "direction": "양방향",
        "phrase": "확인했습니다",
        "reason": "승인/단순 수신 확인 구분 안 됨",
        "candidates": ["승인합니다", "확인했고, 검토 중입니다"],
        "suggestion": "이건 승인인가요, 단순 수신 확인인가요?",
        "verified": False,
    },
    {
        "id": "D04",
        "category": "DECISION_STATUS",
        "direction": "양방향",
        "phrase": "이견 없습니다",
        "reason": "적극 동의 vs 소극적 무이의 구분 안 됨",
        "candidates": ["적극 동의합니다", "특별한 의견 없어 진행에 동의합니다"],
        "suggestion": "적극적으로 동의하시는 건가요, 별다른 의견이 없어 넘어가는 건가요?",
        "verified": False,
    },
    {
        "id": "D05",
        "category": "DECISION_STATUS",
        "direction": "양방향",
        "phrase": "나중에 다시 얘기해요",
        "reason": "결정 보류인지 거절의 완곡 표현인지 모호",
        "candidates": ["일정 시점에 재논의할 결정 보류", "완곡한 거절"],
        "suggestion": "보류 사유와 재논의 예정 시점을 알려주시겠어요?",
        "verified": False,
    },
    {
        "id": "C01",
        "category": "OTHER",
        "direction": "KR→US",
        "phrase": "맥락 설명 없이 결론만 전달",
        "reason": "저맥락 문화권은 배경 설명 부재 시 결정 근거가 부족하다고 느낌",
        "candidates": ["결론만으로 충분", "핵심 근거 1~2줄 추가 필요"],
        "suggestion": "결론에 대한 핵심 근거를 1~2줄 추가하시겠어요?",
        "verified": False,
    },
    {
        "id": "C02",
        "category": "OTHER",
        "direction": "US→KR",
        "phrase": "배경 설명 없이 직접적 지시",
        "reason": "위계/관계 맥락 생략 시 일방적 지시로 느껴질 수 있음",
        "candidates": ["지시 목적과 배경 포함", "간결한 지시만으로 충분"],
        "suggestion": "지시 목적과 배경을 간단히 포함하시겠어요?",
        "verified": False,
    },
    {
        "id": "C03",
        "category": "OTHER",
        "direction": "양방향",
        "phrase": "이모지/느낌표 사용 빈도 차이",
        "reason": "친근함의 신호 vs 진지함 부족 신호로 상반되게 해석",
        "candidates": ["친근함의 표현", "진지함 부족 신호로 오해 위험"],
        "suggestion": "팀 내 톤 가이드라인을 별도로 합의하시겠어요?",
        "verified": False,
    },
    {
        "id": "C04",
        "category": "OTHER",
        "direction": "양방향",
        "phrase": "침묵(응답 없음)",
        "reason": "이의 없음의 신호 vs 미확인 상태로 상반되게 해석",
        "candidates": ["이의 없음(암묵적 동의)", "아직 미확인 상태"],
        "suggestion": "일정 시간 내 무응답 시 처리 규칙을 사전에 합의하시겠어요?",
        "verified": False,
    },
]


def as_few_shot_examples() -> list[dict]:
    return [
        {
            "input": row["phrase"],
            "ambiguity": {
                "span": row["phrase"],
                "category": row["category"],
                "reason": row["reason"],
                "candidates": row["candidates"],
                "suggestion": row["suggestion"],
            },
        }
        for row in CULTURE_CRITERIA
    ]
