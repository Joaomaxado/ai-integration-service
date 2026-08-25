from fastapi import APIRouter, Depends, Query, status

from app.api.auth import verify_service_token
from app.domain.schemas import (
    ClaudeSummarizeRequest,
    JuditConsultRequest,
    JuditConsultResponse,
    SummarizeRequest,
    SummaryResponse,
)
from app.integrations.judit_client import get_judit_client
from app.services.summarization import build_summary, summarize_with_claude

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
