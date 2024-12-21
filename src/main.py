from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from src.api.routers import epics, documents
from src.config import MongoDB, get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(epics.router, prefix="/api/epics", tags=["epics"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting up Ada API...")
    await MongoDB.connect()
    logger.info("Connected to MongoDB")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down Ada API...")
    await MongoDB.disconnect()
    logger.info("Disconnected from MongoDB")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "description": settings.APP_DESCRIPTION,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "epics": "/api/epics",
            "documents": "/api/documents",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }
