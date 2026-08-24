import os
from fastapi import APIRouter, Depends, Header, HTTPException, status
from app.domain.schemas import SummarizeRequest, SummaryResponse, Evidence

router = APIRouter(prefix="/v1/ai", tags=["AI Integration"])

async def verify_service_token(authorization: str | None = Header(default=None)) -> None:
    expected_token = os.getenv("INTERNAL_SERVICE_TOKEN", "segredo-compartilhado-123")
    expected_header = f"Bearer {expected_token}"
    
    if authorization != expected_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas ou ausentes."
        )

@router.post(
    "/summaries",
    response_model=SummaryResponse,
    dependencies=[Depends(verify_service_token)],
    status_code=status.HTTP_200_OK
)
async def create_summary(payload: SummarizeRequest):
    return SummaryResponse(
        request_id=payload.request_id,
        status="completed",
        summary="Resumo gerado automaticamente com base na movimentação.",
        key_points=["Publicação processual", "Prazo regular de 15 dias"],
        evidence=[
            Evidence(
                source_id=payload.movement_id,
                quote="Texto relevante extraído da peça."
            )
        ],
        needs_human_review=True,
        model=os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
        prompt_version="summary-v1",
        error_code=None
    )
