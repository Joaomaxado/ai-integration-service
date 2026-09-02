from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.auth import verify_service_token
from app.domain.schemas import (
    ClaudeSummarizeRequest,
    JuditConsultRequest,
    JuditConsultResponse,
    SummarizeRequest,
    SummaryResponse,
    AuditRequest, AuditResponse, DraftResponse, GenerateDraftRequest,
    IngestDocumentRequest, IngestDocumentResponse, PrecedentRequest, PrecedentResponse,
    TemplateRequest, TemplateResponse,
)
from app.integrations.judit_client import get_judit_client
from app.services.summarization import build_summary, summarize_with_claude
from app.services.legal_workflow import legal_workflow

router = APIRouter(prefix="/v1/ai")
summaries_router = APIRouter(tags=["AI Integration"])
judit_router = APIRouter(prefix="/judit", tags=["Judit"])
claude_router = APIRouter(prefix="/claude", tags=["Claude"])


@summaries_router.post(
    "/summaries",
    response_model=SummaryResponse,
    dependencies=[Depends(verify_service_token)],
    status_code=status.HTTP_200_OK,
)
async def create_summary(payload: SummarizeRequest) -> SummaryResponse:
    return await build_summary(payload)


@claude_router.post(
    "/summaries",
    response_model=SummaryResponse,
    dependencies=[Depends(verify_service_token)],
    status_code=status.HTTP_200_OK,
)
async def create_claude_summary(payload: ClaudeSummarizeRequest) -> SummaryResponse:
    return await summarize_with_claude(
        SummarizeRequest(
            request_id=payload.request_id,
            process_id=payload.process_id,
            movement_id=payload.movement_id,
            operation=payload.operation,
            text=payload.text,
            source=payload.source,
            permissions=payload.permissions,
        )
    )


@judit_router.post(
    "/consult",
    response_model=JuditConsultResponse,
    dependencies=[Depends(verify_service_token)],
    status_code=status.HTTP_200_OK,
)
async def consult_judit(payload: JuditConsultRequest) -> JuditConsultResponse:
    result = await get_judit_client().consult_by_cnj(
        payload.cnj,
        wait_for_result=payload.wait_for_result,
    )
    return JuditConsultResponse(
        request_id=result["request_id"],
        status=result["status"],
        cnj=result["cnj"],
        data=result.get("data"),
    )


@judit_router.get(
    "/requests/{request_id}",
    dependencies=[Depends(verify_service_token)],
    status_code=status.HTTP_200_OK,
)
async def get_judit_request(request_id: str) -> dict:
    return await get_judit_client().get_request(request_id)


@judit_router.get(
    "/responses",
    dependencies=[Depends(verify_service_token)],
    status_code=status.HTTP_200_OK,
)
async def get_judit_responses(
    request_id: str = Query(..., alias="requestId"),
    page: int = Query(default=1, ge=1),
) -> dict:
    return await get_judit_client().get_responses(request_id, page=page)


router.include_router(summaries_router)
router.include_router(judit_router)
router.include_router(claude_router)


legal_router = APIRouter(prefix="/legal", tags=["Legal AI"], dependencies=[Depends(verify_service_token)])


@legal_router.post("/documents", response_model=IngestDocumentResponse)
async def ingest_document(payload: IngestDocumentRequest) -> IngestDocumentResponse:
    document = legal_workflow.rag.ingest(**payload.model_dump())
    return IngestDocumentResponse(document_id=document.document_id, office_id=document.office_id,
                                   chunks=list(document.chunks))


@legal_router.post("/templates", response_model=TemplateResponse)
async def create_template(payload: TemplateRequest) -> TemplateResponse:
    return legal_workflow.save_template(payload)


@legal_router.post("/drafts", response_model=DraftResponse)
async def generate_draft(payload: GenerateDraftRequest) -> DraftResponse:
    try:
        return await legal_workflow.generate_draft(payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@legal_router.post("/precedents", response_model=PrecedentResponse)
async def create_precedent(payload: PrecedentRequest) -> PrecedentResponse:
    return legal_workflow.save_precedent(payload)


@legal_router.post("/audits", response_model=AuditResponse)
async def audit_legal_document(payload: AuditRequest) -> AuditResponse:
    return legal_workflow.audit(payload)


router.include_router(legal_router)
