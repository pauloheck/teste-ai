from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Criação da aplicação FastAPI
app = FastAPI(
    title="GetAI API",
    description="API para processamento assíncrono de documentos e geração de épicos",
    version="1.0.0"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware para logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    
    # Log da requisição
    logger.info(f"Request: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        
        # Log do tempo de resposta
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Response time: {duration:.2f} seconds")
        
        return response
        
    except Exception as e:
        # Log de erro
        logger.error(f"HTTP error: {str(e)}")
        raise

# Include routers
from src.api.routers import documents, epics, stories

# Adiciona os routers
app.include_router(
    documents.router,
    prefix="/api",
    tags=["documents"]
)

app.include_router(
    epics.router,
    prefix="/api/epics",
    tags=["epics"]
)

app.include_router(
    stories.router,
    prefix="/api/stories",
    tags=["stories"]
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Bem-vindo à GetAI API",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
