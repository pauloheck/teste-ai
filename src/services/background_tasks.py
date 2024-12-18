import asyncio
from typing import Optional
import logging
from datetime import datetime
from src.models.document import ProcessingStatus
from src.rag.document_processor import DocumentProcessor
from src.rag.embeddings_manager import EmbeddingsManager
from src.config import MONGODB_URI

logger = logging.getLogger(__name__)

async def process_document_task(
    processing_id: str,
    file_path: str,
    processing_collection,
    document_processor: DocumentProcessor,
    embeddings_manager: EmbeddingsManager
):
    """Background task for processing documents"""
    try:
        logger.info(f"[Task {processing_id}] Starting background processing of document: {file_path}")
        
        # Update status to processing
        processing_collection.update_one(
            {"_id": processing_id},
            {
                "$set": {
                    "status": ProcessingStatus.PROCESSING,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"[Task {processing_id}] Status updated to PROCESSING")
        
        # Process document into chunks
        logger.info(f"[Task {processing_id}] Processing document into chunks...")
        chunks = document_processor.process_file(file_path)
        logger.info(f"[Task {processing_id}] Document processed into {len(chunks)} chunks")
        
        # Generate and store embeddings
        logger.info(f"[Task {processing_id}] Generating and storing embeddings...")
        stored_ids = embeddings_manager.store_embeddings(chunks)
        logger.info(f"[Task {processing_id}] Successfully stored {len(stored_ids)} embeddings")
        
        # Update status to completed
        processing_collection.update_one(
            {"_id": processing_id},
            {
                "$set": {
                    "status": ProcessingStatus.COMPLETED,
                    "updated_at": datetime.utcnow(),
                    "chunks_processed": len(chunks),
                    "embeddings_stored": len(stored_ids)
                }
            }
        )
        logger.info(f"[Task {processing_id}] Processing completed successfully")
        
    except Exception as e:
        error_msg = f"Error processing document: {str(e)}"
        logger.error(f"[Task {processing_id}] {error_msg}")
        
        processing_collection.update_one(
            {"_id": processing_id},
            {
                "$set": {
                    "status": ProcessingStatus.FAILED,
                    "updated_at": datetime.utcnow(),
                    "error_message": error_msg
                }
            }
        )
        logger.error(f"[Task {processing_id}] Status updated to FAILED")
