from fastapi import APIRouter, Depends, status

from app.api.auth import verify_service_token
from app.domain.schemas import SummarizeRequest, SummaryResponse
from app.services.summarization import build_summary

router = APIRouter(prefix="/v1/ai", tags=["AI Integration"])


@router.post(
    "/summaries",
    response_model=SummaryResponse,
    dependencies=[Depends(verify_service_token)],
    status_code=status.HTTP_200_OK,
)
async def create_summary(payload: SummarizeRequest) -> SummaryResponse:
    return build_summary(payload)
