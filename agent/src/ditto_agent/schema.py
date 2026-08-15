from typing import Literal

from pydantic import BaseModel, Field

AmbiguityCategory = Literal["TIME", "REQUEST_INTENT", "DECISION_STATUS", "OTHER"]


class DraftContext(BaseModel):
    sender_tz: str = "Asia/Seoul"
    receiver_tz: str = "America/Los_Angeles"
    receiver_name: str | None = None
    now_iso: str | None = None  # sender's current local time; interface.start() fills this in if omitted


class AmbiguityItem(BaseModel):
    span: str
    category: AmbiguityCategory
    reason: str
    candidates: list[str]
    suggestion: str


class ExtractionResult(BaseModel):
    task: str
    assignee: str | None = None
    deadline_raw: str | None = None
    request_type: str
    decision_status: str
    ambiguities: list[AmbiguityItem] = Field(default_factory=list)


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


class StartResult(BaseModel):
    thread_id: str
    status: Literal["interrupt", "done"]
    interrupt: InterruptPayload | None = None
    card: ConfirmedCard | None = None
