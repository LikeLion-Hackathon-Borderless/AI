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

OUTPUT_SCHEMA_NOTE = """다음 필드를 가진 JSON으로만 응답하세요:
task, assignee(nullable), deadline_raw(nullable), request_type, decision_status,
ambiguities(list of {span, category(TIME|REQUEST_INTENT|DECISION_STATUS|OTHER), reason,
candidates, suggestion})."""


def build_system_prompt() -> str:
    examples = "\n\n".join(
        f"예시 입력: {ex['input']}\n예시 모호성: {ex['ambiguity']}" for ex in FEW_SHOT_EXAMPLES
    )
    return f"{SYSTEM_PRINCIPLE}\n\n{OUTPUT_SCHEMA_NOTE}\n\n[few-shot 예시]\n{examples}"


def build_user_prompt(draft: str, sender_tz: str, receiver_tz: str, now_iso: str) -> str:
    return (
        f"발신자 시간대: {sender_tz} (현재 {now_iso})\n"
        f"수신자 시간대: {receiver_tz}\n"
        f"메시지 초안:\n{draft}"
    )
