# Contrato da API

Base URL: `https://ai-integration-service-5l3r.onrender.com/`

Autenticação em todas as rotas `/v1/ai/*`:

```
Authorization: Bearer <INTERNAL_SERVICE_TOKEN>
Content-Type: application/json
```

OpenAPI: `https://ai-integration-service-5l3r.onrender.com/openapi.json`

## `POST /v1/ai/summaries`

Orquestra Judit (quando `cnj` é informado) e Claude (resumo). Informe `text`, `cnj` ou ambos.

### Request

```json
{
  "requestId": "req-001",
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "processId": "550e8400-e29b-41d4-a716-446655440001",
  "movementId": "movement-456",
  "operation": "summarize",
  "text": "Texto autorizado da movimentação judicial.",
  "cnj": "0000000-00.0000.0.00.0000",
  "source": "pmlex-backend",
  "permissions": ["ai:summarize"]
}
```

### Response 200

```json
{
  "requestId": "req-001",
  "status": "completed",
  "operation": "summarize",
  "summary": "Resumo gerado pelo Claude.",
  "keyPoints": ["Ponto principal identificado no texto."],
  "evidence": [
    {
      "sourceId": "movement-456",
      "quote": "Trecho literal que sustenta o ponto."
    }
  ],
  "uncertainties": [],
  "potentialLegalConsequence": null,
  "humanReviewRequired": true,
  "confidence": "low",
  "model": "claude-3-5-sonnet-20241022",
  "promptVersion": "summary-v1",
  "errorCode": null
}
```

## `POST /v1/ai/claude/summaries`

Resumo direto no Claude, sem consulta Judit. Corpo igual ao summarize, com `text` obrigatório.

## `POST /v1/ai/judit/consult`

Consulta processo na Judit por CNJ.

```json
{
  "cnj": "0000000-00.0000.0.00.0000",
  "waitForResult": true
}
```

## `GET /v1/ai/judit/requests/{request_id}`

Status da requisição assíncrona na Judit.

## `GET /v1/ai/judit/responses?requestId={request_id}`

Resultados da consulta Judit quando o status for `completed`.

### Erros

Corpo padrão:

```json
{
  "timestamp": "2026-08-24T19:00:00.000000+00:00",
  "status": 401,
  "code": "UNAUTHORIZED",
  "message": "Credenciais inválidas ou ausentes.",
  "details": null
}
```

| HTTP | code |
| --- | --- |
| 400 | VALIDATION_ERROR |
| 401 | UNAUTHORIZED |
| 503 | SERVICE_UNAVAILABLE |
