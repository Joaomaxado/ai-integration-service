# ai-integration-service

API FastAPI para o backend Java solicitar resumos de movimentações (Claude) e consultas processuais (Judit).

## Subir o serviço

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.exemple .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Healthcheck: `GET https://ai-integration-service-5l3r.onrender.com/health`

Contrato para o Java: `docs/api-contract.md`

Swagger: `https://ai-integration-service-5l3r.onrender.com/docs`
