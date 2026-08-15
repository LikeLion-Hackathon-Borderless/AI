from dotenv import load_dotenv

from ditto_agent.interface import configure, resume, start
from ditto_agent.schema import (
    AmbiguityItem,
    ConfirmedCard,
    ConflictResult,
    DraftContext,
    ExtractionResult,
    InterruptPayload,
    StartResult,
)

load_dotenv()  # .env가 있으면 OPENAI_API_KEY/DITTO_LLM_MODE를 여기서 읽어들임

__all__ = [
    "AmbiguityItem",
    "ConfirmedCard",
    "ConflictResult",
    "DraftContext",
    "ExtractionResult",
    "InterruptPayload",
    "StartResult",
    "configure",
    "resume",
    "start",
]
