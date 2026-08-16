import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ditto_agent.llm.prompts import (
    TRANSLATE_SYSTEM_PROMPT,
    VERIFY_SYSTEM_PROMPT,
    build_batch_user_prompt,
    build_system_prompt,
    build_translate_user_prompt,
    build_user_prompt,
    build_verify_user_prompt,
)
from ditto_agent.schema import (
    AmbiguityItem,
    AmbiguityList,
    BatchExtractionResult,
    CardTranslation,
    DraftContext,
    ExtractionResult,
)


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
        # 기본값은 "mock"이 아니라 "live" — DITTO_LLM_MODE를 아예 안 정해둔 배포는 조용히
        # 가짜 응답만 내보내는 것보다 키가 없어 바로 죽는 게 훨씬 안전하다(silent failure 방지).
        # 로컬 개발용 mock은 .env.example에 명시적으로 적어둬서 그 경로는 안 바뀜.
        self.mode = os.getenv("DITTO_LLM_MODE", "live")
        if self.mode not in ("mock", "live"):
            raise ValueError(f"DITTO_LLM_MODE must be 'mock' or 'live', got {self.mode!r}")

        self.model = os.getenv("DITTO_OPENAI_MODEL", "gpt-4o-mini")
        self._client = None
        if self.mode == "live":
            from openai import OpenAI

            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENAI_API_KEY가 없는데 DITTO_LLM_MODE=live(기본값)입니다 — "
                    "로컬 개발 중이면 DITTO_LLM_MODE=mock을 .env에 명시하세요."
                )
            # max_retries=0 — 기본값(2)은 429/RPD 한도 초과에도 지수 백오프로 재시도한다.
            # 하루 요청 수 자체가 막힌 상황에서 재시도는 성공 확률 없이 쿼터만 더 태우고
            # 호출 하나당 수십 초씩 조용히 늘어지게 만든다 — 빠르게 실패시키고 호출부
            # (eval/cli.py)가 그 실패를 눈에 보이게 처리하도록 한다.
            # timeout=60.0 — SDK 기본 read timeout은 600초(10분)라, 서버가 느리게 응답하거나
            # 큐잉하면 명확한 에러 없이 최대 10분간 조용히 멈춘다(2026-08-16 세션에서 실측
            # 재현됨). 60초로 줄여서 느린 호출이 빨리 실패하고 호출부가 눈에 보이게 처리하게 함.
            self._client = OpenAI(api_key=api_key, max_retries=0, timeout=60.0)

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

    def verify(self, draft: str, ambiguities: list[AmbiguityItem]) -> list[AmbiguityItem]:
        # 1차 extract()가 flag한 후보를 회의적으로 재검토해 과탐지를 제거하는 2차 호출.
        # mock 모드는 필터링 없이 그대로 통과 — 회귀 테스트에서 그래프 배선만 확인하면 되고,
        # mock 추출기 자체가 이미 최소한의 후보만 내므로 걸러낼 게 없음.
        if self.mode == "mock" or not ambiguities:
            return ambiguities

        completion = self._client.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": VERIFY_SYSTEM_PROMPT},
                {"role": "user", "content": build_verify_user_prompt(draft, [a.model_dump() for a in ambiguities])},
            ],
            response_format=AmbiguityList,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise ValueError("OpenAI가 구조화된 응답을 반환하지 않음 (refusal 등) — completion 로그 확인 필요")
        return parsed.ambiguities

    def extract_batch(self, items: list[tuple[str, DraftContext]]) -> dict[int, ExtractionResult]:
        # 골든셋 평가처럼 서로 무관한 메시지 다수를 한 번에 처리할 때 씀 — 요청 수(RPD) 자체가
        # 쿼터인 계정에서는 메시지당 호출 1개보다 이게 훨씬 아낀다. 실사용 흐름(interface.start())은
        # 항상 메시지 1개라 이 메서드를 안 씀 — 배치는 eval 전용.
        if self.mode == "mock":
            return {i: _mock_extract(draft, ctx) for i, (draft, ctx) in enumerate(items)}

        entries = []
        for i, (draft, ctx) in enumerate(items):
            now_iso = ctx.now_iso or datetime.now(ZoneInfo(ctx.sender_tz)).isoformat()
            entries.append((i, draft, ctx.sender_tz, ctx.receiver_tz, now_iso))

        completion = self._client.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": build_system_prompt(batch=True)},
                {"role": "user", "content": build_batch_user_prompt(entries)},
            ],
            response_format=BatchExtractionResult,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise ValueError("OpenAI가 구조화된 응답을 반환하지 않음 (refusal 등) — completion 로그 확인 필요")
        return {item.index: item.extraction for item in parsed.items}

    def translate_card_fields(
        self, task: str, request_type: str, interpretation_note: str | None, notes: list[str], target_lang: str
    ) -> CardTranslation:
        # 확정된 카드의 자유 텍스트만 옮긴다 — deadline/decision_status/timestamp 등 구조화된
        # 필드는 그대로 둔다(숫자·고정 어휘는 번역 대상이 아니라 프론트 로컬라이즈 대상).
        if self.mode == "mock":
            prefix = f"[{target_lang}] "
            return CardTranslation(
                task=prefix + task,
                request_type=prefix + request_type,
                interpretation_note=(prefix + interpretation_note) if interpretation_note else None,
                notes=[prefix + n for n in notes],
            )

        completion = self._client.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": TRANSLATE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": build_translate_user_prompt(task, request_type, interpretation_note, notes, target_lang),
                },
            ],
            response_format=CardTranslation,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise ValueError("OpenAI가 구조화된 응답을 반환하지 않음 (refusal 등) — completion 로그 확인 필요")
        return parsed
