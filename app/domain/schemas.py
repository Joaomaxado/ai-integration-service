from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID
from pydantic.alias_generators import to_camel

class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

class SummarizeRequest(BaseModel ):
    request_id: str = Field(min_length=1)
    user_id: UUID = Field(min_length=1)
    process_id: UUID = Field(min_length=1)
    movement_id: str = Field(min_length=1)
    operation: str = "summarize"
    text: str = Field(min_length=1)
    event_date: datetime | None = None
    source: str = Field(min_length=1)
    permissions: list[str] = []

class Evidence(BaseModel):
    source_id: str
    quote: str = Field(min_length=1)

class SummaryResponse(BaseModel):
    request_id: str
    status: str
    operation: str
    summary: str | None = None
    key_points: list[str] = []
    evidence: list[Evidence] = []
    uncertainties: list[str] = []
    potential_legal_consequence: str | None = None
    human_review_required: bool = True
    confidence: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    error_code: str | None = None

class Errorresponse(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: int
    code: str
    message: str
    details: str | list[str] | dict | None = None
