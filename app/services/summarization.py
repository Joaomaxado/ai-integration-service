import re
import os
from anthropic import AsyncAnthropic

from app.config import get_settings
from app.domain.schemas import Evidence, SummarizeRequest, SummaryResponse
from app.integrations.claude_client import get_claude_client
from app.integrations.judit_client import get_judit_client, responses_to_text

async def generate_response(self, system: str, user: str):
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system,
            messages=[{"role": "user", "content": user}]
        )
        return response.content[0].text

async def build_summary(payload: SummarizeRequest) -> SummaryResponse:
    source_text, uncertainties, summary_status = await _resolve_source_text(payload)
    if not source_text.strip():
        return SummaryResponse(
            request_id=payload.request_id,
            status=summary_status,
            operation=payload.operation,
            summary=None,
            key_points=[],
            evidence=[],
            uncertainties=uncertainties or ["Não há texto suficiente para resumir."],
            potential_legal_consequence=None,
            human_review_required=True,
            confidence="low",
            model=get_settings().claude_model,
            prompt_version=get_settings().prompt_version,
            error_code="INSUFFICIENT_SOURCE_TEXT",
        )

    claude = await get_claude_client().complete(source_text)
    parsed = parse_claude_output(claude["text"])
    parsed["uncertainties"] = [*uncertainties, *parsed["uncertainties"]]
    if uncertainties:
        parsed["human_review_required"] = True

    return SummaryResponse(
        request_id=payload.request_id,
        status="completed" if summary_status == "completed" else summary_status,
        operation=payload.operation,
        summary=parsed["summary"],
        key_points=parsed["key_points"],
        evidence=parsed["evidence"] or _fallback_evidence(payload, source_text),
        uncertainties=parsed["uncertainties"],
        potential_legal_consequence=parsed["potential_legal_consequence"],
        human_review_required=parsed["human_review_required"],
        confidence=parsed["confidence"],
        model=claude["model"],
        prompt_version=get_settings().prompt_version,
        error_code=None,
    )


async def summarize_with_claude(payload: SummarizeRequest) -> SummaryResponse:
    text = (payload.text or "").strip()
    if not text:
        return SummaryResponse(
            request_id=payload.request_id,
            status="failed",
            operation=payload.operation,
            summary=None,
            human_review_required=True,
            confidence="low",
            model=get_settings().claude_model,
            prompt_version=get_settings().prompt_version,
            error_code="INSUFFICIENT_SOURCE_TEXT",
            uncertainties=["Informe text para resumir com o Claude."],
        )

    claude = await get_claude_client().complete(text)
    parsed = parse_claude_output(claude["text"])
    return SummaryResponse(
        request_id=payload.request_id,
        status="completed",
        operation=payload.operation,
        summary=parsed["summary"],
        key_points=parsed["key_points"],
        evidence=parsed["evidence"] or _fallback_evidence(payload, text),
        uncertainties=parsed["uncertainties"],
        potential_legal_consequence=parsed["potential_legal_consequence"],
        human_review_required=parsed["human_review_required"],
        confidence=parsed["confidence"],
        model=claude["model"],
        prompt_version=get_settings().prompt_version,
        error_code=None,
    )


async def _resolve_source_text(payload: SummarizeRequest) -> tuple[str, list[str], str]:
    parts: list[str] = []
    uncertainties: list[str] = []
    summary_status = "completed"

    if payload.text:
        parts.append(payload.text.strip())

    if payload.cnj:
        consult = await get_judit_client().consult_by_cnj(payload.cnj, wait_for_result=True)
        judit_status = consult.get("status")
        judit_text = responses_to_text(consult.get("data"))
        if judit_text:
            parts.append(f"Dados Judit (CNJ {payload.cnj}):\n{judit_text}")
        if judit_status != "completed":
            summary_status = "pending"
            uncertainties.append(
                f"Consulta Judit ainda não concluída (status={judit_status}, "
                f"request_id={consult.get('request_id')})."
            )
        elif not judit_text:
            uncertainties.append("Consulta Judit concluiu sem dados utilizáveis.")

    return "\n\n".join(part for part in parts if part), uncertainties, summary_status


def _fallback_evidence(payload: SummarizeRequest, text: str) -> list[Evidence]:
    quote = text[:240].strip()
    if not quote:
        return []
    return [Evidence(source_id=payload.movement_id, quote=quote)]


def parse_claude_output(raw: str) -> dict:
    summary = _section(raw, "Resumo") or raw[:400]
    key_points = _bullets(_section(raw, "Pontos principais"))
    uncertainties_text = _section(raw, "Incertezas ou informações insuficientes")
    uncertainties = []
    if uncertainties_text and "Nenhuma incerteza identificada" not in uncertainties_text:
        uncertainties = [uncertainties_text.strip()]

    consequence = _section(raw, "Possível consequência jurídica")
    if consequence and "Nenhuma consequência jurídica potencial" in consequence:
        consequence = None

    review = _section(raw, "Revisão humana necessária")
    human_review = True
    if review:
        human_review = review.strip().upper().startswith("SIM")

    confidence_raw = _section(raw, "Nível de confiança da análise") or ""
    confidence = _map_confidence(confidence_raw)

    return {
        "summary": summary.strip() if summary else None,
        "key_points": key_points,
        "evidence": _parse_evidence(raw),
        "uncertainties": uncertainties,
        "potential_legal_consequence": consequence.strip() if consequence else None,
        "human_review_required": human_review,
        "confidence": confidence,
    }


def _section(raw: str, title: str) -> str | None:
    pattern = rf"{re.escape(title)}:\s*(.*?)(?=\n(?:Pontos principais|Evidências|Incertezas ou informações insuficientes|Possível consequência jurídica|Revisão humana necessária|Nível de confiança da análise|Justificativa do nível de confiança):|\Z)"
    match = re.search(pattern, raw, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return match.group(1).strip()


def _bullets(text: str | None) -> list[str]:
    if not text:
        return []
    items = []
    for line in text.splitlines():
        cleaned = re.sub(r"^[\-\*\d\.\)\s]+", "", line).strip()
        if cleaned:
            items.append(cleaned)
    return items


def _parse_evidence(raw: str) -> list[Evidence]:
    block = _section(raw, "Evidências") or ""
    evidences: list[Evidence] = []
    for match in re.finditer(
        r"Fato:\s*(.*?)\s*Trecho:\s*[\"“]?(.+?)[\"”]?(?=\nFato:|\Z)",
        block,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        quote = match.group(2).strip().strip('"').strip("“”")
        if quote:
            evidences.append(Evidence(source_id="claude", quote=quote[:1000]))
    return evidences


def _map_confidence(value: str) -> str:
    normalized = value.strip().splitlines()[0].upper() if value else ""
    if "ALTO" in normalized:
        return "high"
    if "MÉDIO" in normalized or "MEDIO" in normalized:
        return "medium"
    return "low"
