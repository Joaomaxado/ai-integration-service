import pytest

from app.domain.schemas import AuditRequest, GenerateDraftRequest, PrecedentRequest, TemplateRequest, Traceability
from app.services.legal_workflow import LegalWorkflow


def test_ingestion_chunks_and_isolates_offices():
    workflow = LegalWorkflow()
    workflow.rag.ingest(document_id="doc-1", office_id="office-a", title="A", text="contrato prazo")
    workflow.rag.ingest(document_id="doc-2", office_id="office-b", title="B", text="contrato prazo")

    result = workflow.rag.documents["doc-1"].chunks
    assert result[0].embedding
    assert all(chunk.office_id == "office-a" for chunk in result)


def test_template_generation_returns_citations():
    workflow = LegalWorkflow()
    template = workflow.save_template(TemplateRequest(
        name="Petição", office_id="office-a", content="Pedido: {{SOLICITACAO}}\n{{CONTEXTO}}"))
    workflow.rag.ingest(document_id="doc-1", office_id="office-a", title="Prova", text="fato documentado")

    import asyncio
    draft = asyncio.run(workflow.generate_draft(GenerateDraftRequest(
        office_id="office-a", template_id=template.template_id, request_text="pedir análise",
        document_ids=["doc-1"])))
    assert draft.status == "DRAFT"
    assert draft.citations == ["doc-1:0"]
    assert "pedir análise" in draft.content


def test_precedent_without_source_is_blocked():
    with pytest.raises(ValueError):
        PrecedentRequest(office_id="office-a", title="Precedente", text="texto")


def test_audit_marks_incomplete_traceability_and_conflict():
    first = Traceability(assertion="posse", fact="fato A", proof_id="p1", document_id="d1", location="p. 2")
    second = Traceability(assertion="posse", fact="fato B", proof_id="p2", document_id="d2", location="p. 4")
    incomplete = Traceability(assertion="prazo", fact="fato", proof_id="p3", document_id="d3", location="")
    result = LegalWorkflow().audit(AuditRequest(
        office_id="office-a", document_ids=["d1", "d2", "d3"], assertions=[first, second, incomplete]))

    assert result.status == "C"
    assert {finding.code for finding in result.findings} == {"CONFLICTING_FACTS", "TRACEABILITY_INCOMPLETE"}
    assert {finding.severity for finding in result.findings} == {"ALTO", "CRITICO"}