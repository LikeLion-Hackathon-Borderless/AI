from typing import Literal

from pydantic import BaseModel, Field

AmbiguityCategory = Literal["TIME", "REQUEST_INTENT", "DECISION_STATUS", "OTHER"]


DECISION_STATUS_VOCABULARY: tuple[str, ...] = (
    "최종 확정",
    "임시 시도(재논의 가능)",
    "1차 완료(추가 승인 필요)",
    "제안(결정 아님)",
    "보류",
    "미정",
)


class DraftContext(BaseModel):
    sender_tz: str = "Asia/Seoul"
    receiver_tz: str = "America/Los_Angeles"
    receiver_name: str | None = None
    now_iso: str | None = None  # sender's current local time; interface.start() fills this in if omitted
    receiver_lang: str | None = None  # e.g. "en" — 설정되면 카드의 자유 텍스트 필드를 이 언어로 번역


class AmbiguityItem(BaseModel):
    span: str
    category: AmbiguityCategory
    reason: str
    candidates: list[str]
    suggestion: str


class AmbiguityList(BaseModel):
    ambiguities: list[AmbiguityItem]


class ExtractionResult(BaseModel):
    task: str
    assignee: str | None = None
    deadline_raw: str | None = None
    request_type: str
    decision_status: str
    ambiguities: list[AmbiguityItem] = Field(default_factory=list)


class BatchExtractionItem(BaseModel):
    index: int
    extraction: ExtractionResult


class BatchExtractionResult(BaseModel):
    items: list[BatchExtractionItem]


class BatchAmbiguityItem(BaseModel):
    index: int
    ambiguities: list[AmbiguityItem]


class BatchAmbiguityList(BaseModel):
    items: list[BatchAmbiguityItem]


class InterruptPayload(BaseModel):
    step: int
    total: int
    item: AmbiguityItem


class ConflictResult(BaseModel):
    receiver_local_time: str
    within_working_hours: bool
    note: str | None = None


class ConfirmedCard(BaseModel):
    task: str
    assignee: str | None
    deadline_confirmed: str
    deadline_receiver_local: str
    request_type: str
    decision_status: str
    interpretation_note: str | None
    notes: list[str] = Field(default_factory=list)
    conflict: ConflictResult
    evidence: str


class CardTranslation(BaseModel):
    task: str
    request_type: str
    interpretation_note: str | None
    notes: list[str]


class StartResult(BaseModel):
    thread_id: str
    status: Literal["interrupt", "done"]
    interrupt: InterruptPayload | None = None
    card: ConfirmedCard | None = None
