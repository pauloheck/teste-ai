from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from datetime import datetime
from src.api.routers import epics, documents

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Criação da aplicação FastAPI
app = FastAPI(
    title="Ada API",
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

# Incluir routers
app.include_router(epics.router, prefix="/api/epics", tags=["epics"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])

# Middleware para logging e tratamento de erros
@app.middleware("http")
async def log_and_handle_errors(request: Request, call_next):
    start_time = datetime.now()
    
    try:
        # Log da requisição
        logger.info(f"Request: {request.method} {request.url}")
        
        response = await call_next(request)
        
        # Log do tempo de resposta
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Response time: {duration:.2f} seconds")
        
        return response
        
    except Exception as e:
        # Log de erro
        logger.error(f"HTTP error: {str(e)}")
        return HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/")
async def root():
    """Root endpoint - Retorna informações básicas da API"""
    return {
        "name": "Ada API",
        "description": "Sistema Inteligente para Geração de Projetos",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "epics": "/api/epics",
            "documents": "/api/documents",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }
