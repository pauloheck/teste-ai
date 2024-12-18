from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from src.core.database import init_db, close_db_connections
from src.api.routers import documents, epics, stories
from src.config import validate_config

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
    title="GetAI API",
    description="API for GetAI project",
    version="1.0.0"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique as origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusão dos routers
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(epics.router, prefix="/api", tags=["epics"])
app.include_router(stories.router, prefix="/api", tags=["stories"])

@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da aplicação"""
    await init_db()
    logger.info("Database initialized")
    logger.info("Starting GetAI API...")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado no encerramento da aplicação"""
    await close_db_connections()
    logger.info("Database connections closed")
    logger.info("Shutting down GetAI API...")

@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "Welcome to GetAI API"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
