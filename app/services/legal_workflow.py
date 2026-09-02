from dataclasses import dataclass
from uuid import uuid4

from app.domain.schemas import AuditFinding, AuditRequest, AuditResponse, DraftResponse, PrecedentResponse, TemplateResponse
from app.services.rag_service import RAGService


@dataclass
class LegalWorkflow:
    rag: RAGService

    def __init__(self) -> None:
        self.rag = RAGService()
        self.templates: dict[str, TemplateResponse] = {}
        self.precedents: dict[str, PrecedentResponse] = {}

    def save_template(self, payload) -> TemplateResponse:
        template_id = str(uuid4())
        result = TemplateResponse(template_id=template_id, version=1, **payload.model_dump())
        self.templates[template_id] = result
        return result

    async def generate_draft(self, payload) -> DraftResponse:
        template = self.templates.get(payload.template_id)
        if template is None or template.office_id != payload.office_id:
            raise ValueError("Modelo não encontrado para o escritório")
        context = await self.rag.get_context(payload.request_text, payload.office_id, payload.document_ids)
        citations = [chunk.chunk_id for chunk in context]
        source = "\n\n".join(chunk.text for chunk in context)
        content = template.content.replace("{{SOLICITACAO}}", payload.request_text)
        content = content.replace("{{CONTEXTO}}", source or "Sem contexto documental indexado.")
        return DraftResponse(draft_id=str(uuid4()), template_id=template.template_id,
                             office_id=payload.office_id, content=content, citations=citations)

    def save_precedent(self, payload) -> PrecedentResponse:
        precedent_id = str(uuid4())
        result = PrecedentResponse(precedent_id=precedent_id, **payload.model_dump())
        self.precedents[precedent_id] = result
        return result

    def audit(self, payload: AuditRequest) -> AuditResponse:
        findings: list[AuditFinding] = []
        for assertion in payload.assertions:
            if not assertion.proof_id or not assertion.document_id or not assertion.location:
                findings.append(AuditFinding(severity="CRITICO", code="TRACEABILITY_INCOMPLETE",
                                             message="Afirmação sem rastreabilidade completa.", traceability=assertion))
            elif assertion.document_id not in payload.document_ids:
                findings.append(AuditFinding(severity="ALTO", code="DOCUMENT_NOT_DECLARED",
                                             message="Documento da prova não está no conjunto auditado.", traceability=assertion))
        for first_index, first in enumerate(payload.assertions):
            for second in payload.assertions[first_index + 1:]:
                if (first.assertion and first.assertion == second.assertion
                    and first.document_id and second.document_id
                    and first.document_id != second.document_id
                        and first.fact != second.fact):
                    findings.append(AuditFinding(severity="ALTO", code="CONFLICTING_FACTS",
                                                 message="Documentos/afirmações apresentam fatos conflitantes.",
                                                 traceability=second))
        return AuditResponse(audit_id=str(uuid4()), office_id=payload.office_id,
                             status="C" if findings else "OK", findings=findings)


legal_workflow = LegalWorkflow()