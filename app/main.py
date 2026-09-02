import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.api.routes import router as ai_router
from app.domain.errors import http_exception_handler, validation_exception_handler

# 1. Configuração de Log (TSK-110/118 )
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Gerenciador de Ciclo de Vida (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando AI Integration Service...")
    yield
    logger.info("Encerrando AI Integration Service...")

app = FastAPI(
    title="AI Integration Service",
    version="1.0.0",
    description="API interna para o backend Java solicitar resumos de movimentações, consultas Judit e Claude.",
    lifespan=lifespan
)

# Configuração de CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pmlex.com.br/"], 
    allow_credentials=True,
    allow_methods=["https://pmlex.com.br/"],
    allow_headers=["https://pmlex.com.br/"],
 )

# Handlers de Erro
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler )

# Inclusão de Rotas
app.include_router(ai_router)

@app.get("/health", tags=["Healthcheck"])
async def health_check():
    return {"status": "healthy"}
