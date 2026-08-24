# Contrato da API (consumo pelo backend Java)

Base URL local: `http://localhost:8000`

Autenticação em todas as rotas `/v1/ai/*`:

```
Authorization: Bearer <INTERNAL_SERVICE_TOKEN>
Content-Type: application/json
```

O JSON usa **camelCase** (`requestId`, `processId`). `snake_case` também é aceito na entrada.

OpenAPI: `http://localhost:8000/openapi.json`

## `POST /v1/ai/summaries`

### Request

```json
{
  "requestId": "req-001",
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "processId": "550e8400-e29b-41d4-a716-446655440001",
  "movementId": "movement-456",
  "operation": "summarize",
  "text": "Texto autorizado da movimentação judicial.",
  "source": "pmlex-backend",
  "permissions": ["ai:summarize"]
}
```

`userId` é opcional. `processId` e `movementId` são strings.

### Response 200

```json
{
  "requestId": "req-001",
  "status": "completed",
  "operation": "summarize",
  "summary": "Resumo curto baseado no texto fornecido.",
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
  "model": "local-stub",
  "promptVersion": "summary-v1",
  "errorCode": null
}
```

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
