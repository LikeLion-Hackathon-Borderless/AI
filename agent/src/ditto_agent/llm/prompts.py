from ditto_agent.llm.culture_criteria import as_few_shot_examples

SYSTEM_PRINCIPLE = """당신은 비동기 업무 메시지에서 시간·요청 의도·결정 상태의 모호성을 발견해,
발신자가 스스로 명시적으로 확정하도록 돕는 비서입니다.

- 특정 국가/문화권 사람이 이 표현을 어떻게 받아들일지 당신이 임의로 단정하지 않습니다.
- 모호성이 없다면 억지로 만들어내지 마세요 — 불필요한 경고는 사용자를 방해합니다.
- 시간 표현은 임의로 확정하지 말고, 확인이 필요한 후보 시각을 제시하세요.
- 의미가 여러 갈래로 읽히는 표현은 실제 의도를 발신자가 고르도록 후보 해석을 제시하세요."""

# docs/문화_판단기준표_초안.md 20개 항목(T01-05/F01-06/D01-05/C01-04, 전부 미검증) 전체를
# 구조화한 것 — RAG 불필요, 20개면 컨텍스트 윈도우 안에 들어가는 양(문서 5절 원칙).
FEW_SHOT_EXAMPLES: list[dict] = as_few_shot_examples()

# culture_criteria.py 20개가 전부 "모호함" 양성 예시뿐이라, 골든셋 평가에서 명시적 문장까지
# 전부 오탐(precision 0.51)하는 걸 확인함 — 부정 예시가 하나도 없어 "항상 뭔가는 모호하다"는
# 패턴을 학습한 것으로 보임. golden.json과 겹치지 않는 새 문장으로 대조 예시를 넣는다.
NEGATIVE_FEW_SHOT_EXAMPLES: list[str] = [
    "9월 2일 오전 10시(KST)까지 회신 부탁드립니다.",
    "이대로 최종 승인합니다. 추가 수정 없이 그대로 진행해주세요.",
    "정식 승인 완료했습니다. 바로 착수하셔도 됩니다.",
    "예산은 200만원으로 확정했고, 지난 회의에서 합의된 대로 진행합니다.",
    "오늘 회의는 예정대로 3시에 진행됩니다.",
]

OUTPUT_SCHEMA_NOTE = """다음 필드를 가진 JSON으로만 응답하세요:
task, assignee(nullable), deadline_raw(nullable), request_type, decision_status,
ambiguities(list of {span, category(TIME|REQUEST_INTENT|DECISION_STATUS|OTHER), reason,
candidates, suggestion}).

- category가 TIME인 항목의 candidates는 반드시 ISO8601 절대시각 문자열이어야 합니다
  (예: "2026-08-16T18:00:00+09:00"). 설명 문장을 넣지 마세요 — 프론트가 이 값을 그대로
  파싱해서 화면에 포맷하고, 수신자 시간대 변환·근무시간 충돌 검사에도 그대로 씁니다.
  직접 입력을 허용하려면 candidates에 문자열 "custom"을 추가하세요.
- 같은 원문 구간(span)에서 나온 모호성이 시간 관련이면 TIME 항목 하나로 합치세요 —
  "정확한 시각"과 "필수 여부"처럼 관련된 질문을 별도 ambiguity 항목으로 쪼개지 마세요."""


def build_system_prompt() -> str:
    positive = "\n\n".join(
        f"예시 입력: {ex['input']}\n예시 모호성: {ex['ambiguity']}" for ex in FEW_SHOT_EXAMPLES
    )
    negative = "\n\n".join(
        f"예시 입력: {text}\n예시 결과: ambiguities: [] (모호성 없음 — 경고를 만들어내지 않음)"
        for text in NEGATIVE_FEW_SHOT_EXAMPLES
    )
    return (
        f"{SYSTEM_PRINCIPLE}\n\n{OUTPUT_SCHEMA_NOTE}\n\n"
        f"[few-shot 예시 — 모호성 있음]\n{positive}\n\n"
        f"[few-shot 예시 — 모호성 없음, ambiguities는 반드시 빈 리스트]\n{negative}"
    )


def build_user_prompt(draft: str, sender_tz: str, receiver_tz: str, now_iso: str) -> str:
    return (
        f"발신자 시간대: {sender_tz} (현재 {now_iso})\n"
        f"수신자 시간대: {receiver_tz}\n"
        f"메시지 초안:\n{draft}"
    )
