import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ditto_agent.llm.prompts import build_system_prompt, build_user_prompt
from ditto_agent.schema import AmbiguityItem, DraftContext, ExtractionResult


def _mock_deadline_raw(draft: str) -> str | None:
    if "내일" in draft:
        return "내일까지"
    idx = draft.find("까지")
    if idx == -1:
        return None
    tokens = draft[:idx].split()
    return " ".join(tokens[-3:]) + "까지"


def _mock_extract(draft: str, context: DraftContext) -> ExtractionResult:
    now = datetime.fromisoformat(context.now_iso) if context.now_iso else datetime.now(ZoneInfo(context.sender_tz))
    ambiguities: list[AmbiguityItem] = []
    deadline_raw = _mock_deadline_raw(draft)

    if "내일" in draft:
        tomorrow_18 = (now + timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)
        ambiguities.append(
            AmbiguityItem(
                span="내일까지",
                category="TIME",
                reason="상대적 기한 표현이라 기준 시각이 명시되지 않음",
                candidates=[tomorrow_18.isoformat(), "custom"],
                suggestion=(
                    f"'내일까지'의 정확한 기준 시각이 필요합니다 — "
                    f"{tomorrow_18.strftime('%m/%d %H:%M')} {context.sender_tz} 기준으로 확정할까요?"
                ),
            )
        )

    if "고민" in draft or "재검토" in draft:
        ambiguities.append(
            AmbiguityItem(
                span=draft.strip(),
                category="REQUEST_INTENT",
                reason="완곡한 의견 제시가 여러 의도로 읽힐 수 있음",
                candidates=["현재 방향 유지 + 세부 보완 요청", "완곡한 반대", "추가 논의 요청"],
                suggestion="실제 의도를 선택해주세요.",
            )
        )

    return ExtractionResult(
        task="문서 검토",
        assignee=context.receiver_name,
        deadline_raw=deadline_raw,
        request_type="검토 요청",
        decision_status="필수 반영" if ambiguities else "제안",
        ambiguities=ambiguities,
    )


class LLMClient:
    def __init__(self) -> None:
        self.mode = os.getenv("DITTO_LLM_MODE", "mock")
        if self.mode not in ("mock", "live"):
            raise ValueError(f"DITTO_LLM_MODE must be 'mock' or 'live', got {self.mode!r}")

        self.model = os.getenv("DITTO_OPENAI_MODEL", "gpt-5")
        self._client = None
        if self.mode == "live":
            from openai import OpenAI

            self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def extract(self, draft: str, context: DraftContext) -> ExtractionResult:
        if self.mode == "mock":
            return _mock_extract(draft, context)

        now_iso = context.now_iso or datetime.now(ZoneInfo(context.sender_tz)).isoformat()
        completion = self._client.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": build_user_prompt(draft, context.sender_tz, context.receiver_tz, now_iso)},
            ],
            response_format=ExtractionResult,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise ValueError("OpenAI가 구조화된 응답을 반환하지 않음 (refusal 등) — completion 로그 확인 필요")
        return parsed
