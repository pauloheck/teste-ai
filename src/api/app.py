from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from datetime import datetime
from src.api.routers import epics, documents, stories
from src.config import validate_config
from src.config.database import init_db, close_db_connections

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Validate configuration
validate_config()

# Criação da aplicação FastAPI
app = FastAPI(
    title="Ada API",
    description="API para processamento assíncrono de documentos e geração de épicos",
    version="1.0.0",
    openapi_url="/ada_dev"
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
app.include_router(stories.router, prefix="/api/stories", tags=["stories"])

# Eventos de inicialização e encerramento
@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da aplicação"""
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado no encerramento da aplicação"""
    await close_db_connections()

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
        logger.error(f"Error processing request: {str(e)}")
        return HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint - Retorna informações básicas da API"""
    return {
        "name": "Ada API",
        "version": "1.0.0",
        "endpoints": {
            "epics": "/api/epics",
            "documents": "/api/documents",
            "stories": "/api/stories",
            "docs": "/docs",
            "openapi": "/ada_dev"
        }
    }
