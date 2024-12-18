import asyncio
from datetime import datetime
from typing import Optional, List, Tuple
import logging
from bson import ObjectId
from pymongo import MongoClient
import hashlib
from pathlib import Path
from src.models.document import DocumentProcessing, ProcessingStatus
from src.rag.document_processor import DocumentProcessor
from src.rag.embeddings_manager import EmbeddingsManager
from src.config import MONGODB_URI
from src.services.background_manager import BackgroundTaskManager
from pymongo import IndexModel, ASCENDING

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
        self._ensure_indexes()

    def _ensure_indexes(self):
        """Ensure all required indexes exist"""
        try:
            # Drop existing file_hash index if it exists
            self.processing_collection.drop_index("file_hash_1")
        except:
            pass  # Index might not exist

        # Create indexes
        indexes = [
            IndexModel([("status", ASCENDING)]),
            IndexModel([("created_at", ASCENDING)]),
            IndexModel([("filename", ASCENDING)]),
            # Unique index on file_hash, but ignore null values
            IndexModel(
                [("file_hash", ASCENDING)],
                unique=True,
                partialFilterExpression={"file_hash": {"$type": "string"}}
            )
        ]
        self.processing_collection.create_indexes(indexes)

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read the file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def check_duplicate_document(self, filename: str, file_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if a document already exists by filename or content hash.
        Returns (is_duplicate, existing_id, status_message)
        """
        # Check by filename first (quick check)
        existing_doc = self.processing_collection.find_one({"filename": filename})
        if existing_doc:
            doc_id = str(existing_doc["_id"])
            return True, doc_id, f"Document with filename '{filename}' already exists (ID: {doc_id})"

        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)
        
        # Check by content hash
        existing_doc = self.processing_collection.find_one({"file_hash": file_hash})
        if existing_doc:
            doc_id = str(existing_doc["_id"])
            return True, doc_id, f"Document with identical content already exists (ID: {doc_id}, filename: {existing_doc['filename']})"

        return False, None, None

    async def create_processing_record(self, filename: str, file_path: str) -> DocumentProcessing:
        """Create a new document processing record"""
        # Calculate file hash
        file_hash = self._calculate_file_hash(file_path)
        
        is_duplicate, existing_id, status_message = await self.check_duplicate_document(filename, file_path)
        if is_duplicate:
            raise ValueError(status_message)

        doc = {
            "filename": filename,
            "file_path": file_path,
            "file_hash": file_hash,
            "status": ProcessingStatus.PENDING,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        try:
            result = self.processing_collection.insert_one(doc)
            doc["id"] = str(result.inserted_id)
            return DocumentProcessing(**doc)
        except Exception as e:
            if "duplicate key error" in str(e):
                existing_doc = self.processing_collection.find_one({"file_hash": file_hash})
                if existing_doc:
                    raise ValueError(f"Document already exists with ID: {existing_doc['_id']}")
            raise

    def _process_document_sync(self, processing_id: str):
        """Synchronous document processing function"""
        try:
            # Get processing record
            record = self.processing_collection.find_one({"_id": ObjectId(processing_id)})
            if not record:
                logger.error(f"[SYNC] Processing record not found: {processing_id}")
                return

            # Update status to processing
            self.update_processing_status(processing_id, ProcessingStatus.PROCESSING)
            logger.info(f"[SYNC] Started processing document {processing_id}")

            # Process document
            logger.info(f"[SYNC] Processing file: {record['file_path']}")
            chunks = self.document_processor.process_file(record["file_path"])
            logger.info(f"[SYNC] Generated {len(chunks)} chunks")

            # Store embeddings
            logger.info(f"[SYNC] Storing embeddings for {len(chunks)} chunks")
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
