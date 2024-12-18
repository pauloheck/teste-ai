from fastapi import APIRouter, HTTPException, status, UploadFile, File, Query, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from typing import List, Optional
import logging
import os
import time
import aiofiles
from pathlib import Path
from src.models.document import DocumentProcessingResponse, ProcessingStatus
from src.services.document_service import DocumentService

logger = logging.getLogger(__name__)

router = APIRouter()
document_service = DocumentService()

# Ensure upload directory exists
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/documents/processing")
async def list_processing_status(
    status: Optional[ProcessingStatus] = Query(None, description="Filter by processing status")
) -> List[DocumentProcessingResponse]:
    """
    List all document processing records, optionally filtered by status
    """
    try:
        records = await document_service.list_processing_status(status)
        return [
            DocumentProcessingResponse(
                id=record.id,
                filename=record.filename,
                status=record.status,
                message=f"Document processing {record.status}"
            )
            for record in records
        ]
    except Exception as e:
        logger.error(f"Error listing processing status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing processing status: {str(e)}"
        )

@router.get("/documents/processing/{processing_id}")
async def get_processing_status(processing_id: str) -> DocumentProcessingResponse:
    """
    Get the status of a specific document processing
    """
    try:
        record = await document_service.get_processing_status(processing_id)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Processing record not found: {processing_id}"
            )
        
        return DocumentProcessingResponse(
            id=record.id,
            filename=record.filename,
            status=record.status,
            message=f"Document processing {record.status}"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error getting processing status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting processing status: {str(e)}"
        )

@router.post("/documents/retry-failed")
async def retry_failed_documents():
    """
    Retry processing all failed documents
    """
    try:
        await document_service.retry_failed_documents()
        return {"message": "Retry initiated for failed documents"}
    except Exception as e:
        logger.error(f"Error retrying failed documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrying failed documents: {str(e)}"
        )

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    request: Request = Request
):
    """
    Upload a new document and initiate asynchronous processing
    """
    start_time = time.time()
    logger.info(f"[UPLOAD] Started upload request for file: {file.filename}")
    
    try:
        # Validate file extension
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in ['.txt', '.pdf', '.md', '.csv', '.xlsx', '.xls']:
            logger.warning(f"[UPLOAD] Unsupported file extension: {file_extension}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file extension: {file_extension}"
            )
        
        # Save uploaded file to temporary location first
        temp_file_path = UPLOAD_DIR / f"temp_{file.filename}"
        logger.info(f"[UPLOAD] Saving file to temporary location: {temp_file_path}")
        save_start = time.time()
        
        # Salvar arquivo de forma assíncrona
        content = await file.read()
        async with aiofiles.open(str(temp_file_path), "wb") as buffer:
            await buffer.write(content)
            
        logger.info(f"[UPLOAD] File saved in {time.time() - save_start:.2f} seconds")
        
        # Check for duplicates
        try:
            is_duplicate, existing_id, message = await document_service.check_duplicate_document(
                filename=file.filename,
                file_path=str(temp_file_path)
            )
            
            if is_duplicate:
                logger.warning(f"[UPLOAD] Duplicate document detected: {message}")
                # Remove temporary file
                temp_file_path.unlink()
                
                # Get base URL from request
                base_url = str(request.base_url)
                
                return {
                    "status": "duplicate",
                    "message": message,
                    "existing_document": {
                        "id": existing_id,
                        "links": {
                            "details": f"{base_url}api/documents/{existing_id}",
                            "status": f"{base_url}api/documents/{existing_id}/status",
                            "download": f"{base_url}api/documents/{existing_id}/download"
                        }
                    }
                }

        except Exception as e:
            # Remove temporary file in case of error
            temp_file_path.unlink()
            raise e
        
        # Move file to final location
        final_file_path = UPLOAD_DIR / file.filename
        temp_file_path.rename(final_file_path)
        
        # Create processing record
        logger.info("[UPLOAD] Creating processing record...")
        record_start = time.time()
        try:
            processing_record = await document_service.create_processing_record(
                filename=file.filename,
                file_path=str(final_file_path)
            )
            logger.info(f"[UPLOAD] Processing record created in {time.time() - record_start:.2f} seconds. ID: {processing_record.id}")
        except ValueError as ve:
            # If we get a duplicate error here, it means another request uploaded the same file
            # between our check and insert
            logger.warning(f"[UPLOAD] Duplicate detected during record creation: {str(ve)}")
            final_file_path.unlink()  # Remove the uploaded file
            return {
                "status": "duplicate",
                "message": str(ve),
                "existing_document": {
                    "id": str(ve).split("ID: ")[1],
                    "links": {
                        "details": f"{request.base_url}api/documents/{str(ve).split('ID: ')[1]}",
                        "status": f"{request.base_url}api/documents/{str(ve).split('ID: ')[1]}/status",
                        "download": f"{request.base_url}api/documents/{str(ve).split('ID: ')[1]}/download"
                    }
                }
            }
        
        # Queue document for background processing
        logger.info(f"[UPLOAD] Queueing document for processing: {processing_record.id}")
        background_tasks.add_task(
            document_service.process_document,
            str(processing_record.id)
        )

        total_time = time.time() - start_time
        logger.info(f"[UPLOAD] Request completed in {total_time:.2f} seconds")
        
        # Get base URL from request
        base_url = str(request.base_url)
        
        return {
            "status": "success",
            "message": "Document uploaded successfully",
            "document": {
                "id": str(processing_record.id),
                "filename": processing_record.filename,
                "status": processing_record.status,
                "links": {
                    "details": f"{base_url}api/documents/{processing_record.id}",
                    "status": f"{base_url}api/documents/{processing_record.id}/status",
                    "download": f"{base_url}api/documents/{processing_record.id}/download"
                }
            }
        }
            
    except HTTPException as he:
        logger.error(f"[UPLOAD] HTTP Exception after {time.time() - start_time:.2f} seconds: {str(he)}")
        raise he
    except Exception as e:
        error_msg = f"Error uploading document: {str(e)}"
        logger.error(f"[UPLOAD] Error after {time.time() - start_time:.2f} seconds: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
