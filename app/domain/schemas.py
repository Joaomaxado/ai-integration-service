from datetime import datetime, timezone
from typing import Any
from uuid import UUID
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class LegalPoint(BaseModel):
    text: str
    status: Literal['V', 'I', 'U', 'C', 'N']
    confidence: Literal['low', 'medium', 'high']
    evidence_quote: str

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
    text: str | None = Field(
        default=None,
        min_length=1,
        examples=["Texto autorizado da movimentação judicial."],
    )
    cnj: str | None = Field(default=None, examples=["0000000-00.0000.0.00.0000"])
    event_date: datetime | None = None
    source: str = Field(min_length=1, examples=["pmlex-backend"])
    permissions: list[str] = Field(default_factory=list, examples=[["ai:summarize"]])

    @model_validator(mode="after")
    def require_text_or_cnj(self):
        if not (self.text or self.cnj):
            raise ValueError("Informe text e/ou cnj.")
        return self


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


class ClaudeSummarizeRequest(CamelModel):
    request_id: str = Field(min_length=1, examples=["req-001"])
    process_id: str = Field(min_length=1, examples=["550e8400-e29b-41d4-a716-446655440001"])
    movement_id: str = Field(min_length=1, examples=["movement-456"])
    operation: str = Field(default="summarize")
    text: str = Field(min_length=1, examples=["Texto autorizado da movimentação judicial."])
    source: str = Field(min_length=1, examples=["pmlex-backend"])
    permissions: list[str] = Field(default_factory=list, examples=[["ai:summarize"]])


class JuditConsultRequest(CamelModel):
    cnj: str = Field(min_length=1, examples=["0000000-00.0000.0.00.0000"])
    wait_for_result: bool = True


class JuditConsultResponse(CamelModel):
    request_id: str
    status: str
    cnj: str
    data: dict[str, Any] | list | None = None


class ErrorResponse(CamelModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: int
    code: str
    message: str
    details: str | list | dict | None = None
