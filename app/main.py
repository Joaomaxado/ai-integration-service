from fastapi import FastAPI, Request, status
from datetime import datetime
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.api.routes import router as ai_router

app = FastAPI(
    title='Ai Integration Service',
    version='1.0.0')

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": 400,
            "code": "VALIDATION_ERROR",
            "message": "Os dados fornecidos são inválidos.",
            "details": exc.errors()
        }
    )
@app.get("/health", tags=["Healthcheck"])
async def health_check():
    return {"status": "healthy"}

app.include_router(ai_router)