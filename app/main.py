from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import router as ai_router
from app.domain.errors import http_exception_handler, validation_exception_handler

load_dotenv()

app = FastAPI(
    title="AI Integration Service",
    version="1.0.0",
    description="API interna para o backend Java solicitar resumos de movimentações, consultas Judit e Claude.",
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.include_router(ai_router)


@app.get("/health", tags=["Healthcheck"])
async def health_check():
    return {"status": "healthy"}
