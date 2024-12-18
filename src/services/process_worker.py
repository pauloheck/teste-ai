import asyncio
import logging
from datetime import datetime
from bson import ObjectId
from src.models.document import ProcessingStatus
from src.rag.document_processor import DocumentProcessor
from src.rag.embeddings_manager import EmbeddingsManager
from src.config import MONGODB_URI

logger = logging.getLogger(__name__)

async def process_document_worker():
    """Background worker to process documents"""
    from src.services.document_service import DocumentService
    service = DocumentService()
    
    while True:
        try:
            # Find pending documents
            pending_docs = service.processing_collection.find(
                {"status": ProcessingStatus.PENDING}
            )
            
            for doc in pending_docs:
                processing_id = str(doc["_id"])
                file_path = doc["file_path"]
                
                try:
                    logger.info(f"[WORKER] Starting to process document {processing_id}")
                    
                    # Update status to processing
                    service.update_processing_status(processing_id, ProcessingStatus.PROCESSING)
                    
                    # Process document
                    chunks = service.document_processor.process_file(file_path)
                    logger.info(f"[WORKER] Document {processing_id} processed into {len(chunks)} chunks")
                    
                    # Store embeddings
                    stored_ids = service.embeddings_manager.store_embeddings(chunks)
                    logger.info(f"[WORKER] Stored {len(stored_ids)} embeddings for document {processing_id}")
                    
                    # Update status to completed
                    service.update_processing_status(
                        processing_id,
                        ProcessingStatus.COMPLETED,
                        chunks_processed=len(chunks),
                        embeddings_stored=len(stored_ids)
                    )
                    logger.info(f"[WORKER] Document {processing_id} processing completed")
                    
                except Exception as e:
                    error_msg = f"Error processing document: {str(e)}"
                    logger.error(f"[WORKER] {error_msg}")
                    service.update_processing_status(
                        processing_id,
                        ProcessingStatus.FAILED,
                        error_message=error_msg
                    )
            
            # Wait before checking for new documents
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"[WORKER] Error in worker loop: {str(e)}")
            await asyncio.sleep(5)  # Wait longer on error
