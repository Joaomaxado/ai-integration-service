from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

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


class Chunk(CamelModel):
    chunk_id: str
    document_id: str
    office_id: str
    text: str
    position: int
    embedding: list[float]


class IngestDocumentRequest(CamelModel):
    document_id: str = Field(min_length=1)
    office_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    source_url: str | None = None


class IngestDocumentResponse(CamelModel):
    document_id: str
    office_id: str
    chunks: list[Chunk]


class TemplateRequest(CamelModel):
    name: str = Field(min_length=1)
    office_id: str = Field(min_length=1)
    content: str = Field(min_length=1)
    status: Literal["DRAFT", "APPROVED"] = "DRAFT"


class TemplateResponse(TemplateRequest):
    template_id: str
    version: int


class GenerateDraftRequest(CamelModel):
    office_id: str = Field(min_length=1)
    template_id: str
    request_text: str = Field(min_length=1)
    document_ids: list[str] = Field(default_factory=list)


class DraftResponse(CamelModel):
    draft_id: str
    template_id: str
    office_id: str
    status: Literal["DRAFT"] = "DRAFT"
    content: str
    citations: list[str] = Field(default_factory=list)


class PrecedentRequest(CamelModel):
    office_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    source_url: str | None = None
    source_citation: str | None = None

    @model_validator(mode="after")
    def require_verifiable_source(self):
        if not (self.source_url or self.source_citation):
            raise ValueError("Precedente exige source_url ou source_citation verificável.")
        return self


class PrecedentResponse(PrecedentRequest):
    precedent_id: str
    status: Literal["PRE"] = "PRE"


class Traceability(CamelModel):
    assertion: str | None = None
    fact: str | None = None
    proof_id: str | None = None
    document_id: str | None = None
    location: str | None = None


class AuditFinding(CamelModel):
    severity: Literal["CRITICO", "ALTO", "MEDIO", "BAIXO"]
    code: str
    message: str
    traceability: Traceability | None = None


class AuditRequest(CamelModel):
    office_id: str = Field(min_length=1)
    document_ids: list[str] = Field(default_factory=list)
    assertions: list[Traceability] = Field(default_factory=list)


class AuditResponse(CamelModel):
    audit_id: str
    office_id: str
    status: Literal["OK", "C"]
    findings: list[AuditFinding] = Field(default_factory=list)
