from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class SummarizeRequest(CamelModel):
    request_id: str = Field(min_length=1, examples=["req-001"])
    user_id: UUID | None = Field(default=None, examples=["550e8400-e29b-41d4-a716-446655440000"])
    process_id: str = Field(min_length=1, examples=["550e8400-e29b-41d4-a716-446655440001"])
    movement_id: str = Field(min_length=1, examples=["movement-456"])
    operation: str = Field(default="summarize")
    text: str = Field(min_length=1, examples=["Texto autorizado da movimentação judicial."])
    event_date: datetime | None = None
    source: str = Field(min_length=1, examples=["pmlex-backend"])
    permissions: list[str] = Field(default_factory=list, examples=[["ai:summarize"]])


class Evidence(CamelModel):
    source_id: str
    quote: str = Field(min_length=1)


class SummaryResponse(CamelModel):
    request_id: str
    status: str
    operation: str
    summary: str | None = None
    key_points: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    potential_legal_consequence: str | None = None
    human_review_required: bool = True
    confidence: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    error_code: str | None = None


class ErrorResponse(CamelModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: int
    code: str
    message: str
    details: str | list | dict | None = None
