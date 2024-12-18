import asyncio
from datetime import datetime
from typing import Optional, List
import logging
from bson import ObjectId
from pymongo import MongoClient
from src.models.document import DocumentProcessing, ProcessingStatus
from src.rag.document_processor import DocumentProcessor
from src.rag.embeddings_manager import EmbeddingsManager
from src.config import MONGODB_URI
from src.services.background_manager import BackgroundTaskManager

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client.getai
        self.processing_collection = self.db.document_processing
        self.document_processor = DocumentProcessor()
        self.embeddings_manager = EmbeddingsManager(mongodb_uri=MONGODB_URI)
        self.background_manager = BackgroundTaskManager()
        
        # Ensure indexes
        self.processing_collection.create_index("status")
        self.processing_collection.create_index("created_at")
        self.processing_collection.create_index("filename")

    def _process_document_sync(self, processing_id: str):
        """Synchronous document processing function"""
        logger.info(f"[SYNC] Starting synchronous processing of document {processing_id}")
        try:
            # Get processing record
            record = self.processing_collection.find_one({"_id": ObjectId(processing_id)})
            if not record:
                logger.error(f"[SYNC] Processing record not found: {processing_id}")
                return

            # Update status to processing
            self.update_processing_status(processing_id, ProcessingStatus.PROCESSING)
            logger.info(f"[SYNC] Updated status to PROCESSING for {processing_id}")

            # Process document
            logger.info(f"[SYNC] Processing file: {record['file_path']}")
            chunks = self.document_processor.process_file(record["file_path"])
            logger.info(f"[SYNC] Generated {len(chunks)} chunks")

            logger.info(f"[SYNC] Storing embeddings for {processing_id}")
            stored_ids = self.embeddings_manager.store_embeddings(chunks)
            logger.info(f"[SYNC] Stored {len(stored_ids)} embeddings")

            # Update status to completed
            self.update_processing_status(
                processing_id,
                ProcessingStatus.COMPLETED,
                chunks_processed=len(chunks),
                embeddings_stored=len(stored_ids)
            )
            logger.info(f"[SYNC] Document {processing_id} completed successfully")

        except Exception as e:
            error_msg = f"Error processing document: {str(e)}"
            logger.error(f"[SYNC] {error_msg}")
            self.update_processing_status(
                processing_id,
                ProcessingStatus.FAILED,
                error_message=error_msg
            )

    async def create_processing_record(self, filename: str, file_path: str) -> DocumentProcessing:
        """Create a new document processing record"""
        doc = {
            "filename": filename,
            "file_path": file_path,
            "status": ProcessingStatus.PENDING,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = self.processing_collection.insert_one(doc)
        doc["id"] = str(result.inserted_id)
        return DocumentProcessing(**doc)

    def update_processing_status(
        self,
        processing_id: str,
        status: ProcessingStatus,
        error_message: Optional[str] = None,
        chunks_processed: Optional[int] = None,
        embeddings_stored: Optional[int] = None
    ):
        """Update the processing status of a document"""
        update_doc = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if error_message is not None:
            update_doc["error_message"] = error_message
        if chunks_processed is not None:
            update_doc["chunks_processed"] = chunks_processed
        if embeddings_stored is not None:
            update_doc["embeddings_stored"] = embeddings_stored

        self.processing_collection.update_one(
            {"_id": ObjectId(processing_id)},
            {"$set": update_doc}
        )

    async def process_document(self, processing_id: str):
        """Queue document for background processing"""
        logger.info(f"[ASYNC] Queueing document {processing_id} for background processing")
        self.background_manager.add_task(self._process_document_sync, processing_id)
        logger.info(f"[ASYNC] Document {processing_id} queued successfully")

    async def get_processing_status(self, processing_id: str) -> Optional[DocumentProcessing]:
        """Get the current status of a document processing"""
        record = self.processing_collection.find_one({"_id": ObjectId(processing_id)})
        if record:
            record["id"] = str(record.pop("_id"))
            return DocumentProcessing(**record)
        return None

    async def list_processing_status(self, status: Optional[ProcessingStatus] = None) -> List[DocumentProcessing]:
        """List all document processing records, optionally filtered by status"""
        query = {}
        if status:
            query["status"] = status

        records = self.processing_collection.find(query).sort("created_at", -1)
        return [
            DocumentProcessing(**{**record, "id": str(record.pop("_id"))})
            for record in records
        ]

    async def retry_failed_documents(self):
        """Retry processing of all failed documents"""
        failed_records = self.processing_collection.find({"status": ProcessingStatus.FAILED})
        for record in failed_records:
            processing_id = str(record["_id"])
            logger.info(f"[ASYNC] Requeueing failed document {processing_id}")
            await self.process_document(processing_id)
