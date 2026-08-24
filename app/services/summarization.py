import os

from app.domain.schemas import Evidence, SummarizeRequest, SummaryResponse


def build_summary(payload: SummarizeRequest) -> SummaryResponse:
    text = payload.text.strip()
    first_sentence = text.split(".")[0].strip()
    summary = first_sentence[:400] if first_sentence else text[:400]
    quote = text[:240]

    return SummaryResponse(
        request_id=payload.request_id,
        status="completed",
        operation=payload.operation,
        summary=summary,
        key_points=[summary] if summary else [],
        evidence=[
            Evidence(
                source_id=payload.movement_id,
                quote=quote or text,
            )
        ],
        uncertainties=[],
        potential_legal_consequence=None,
        human_review_required=True,
        confidence="low",
        model=os.getenv("CLAUDE_MODEL", "local-stub"),
        prompt_version="summary-v1",
        error_code=None,
    )
