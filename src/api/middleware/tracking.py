"""
Middleware for API request tracking
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import json
from src.services.tracking_service import TrackingService
from src.models.tracking import APITracking, TrackingType

class APITrackingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, tracking_service: TrackingService):
        super().__init__(app)
        self.tracking_service = tracking_service

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Capture request body safely
        try:
            request_body = await request.json() if request.method in ["POST", "PUT", "PATCH"] else None
        except json.JSONDecodeError:
            request_body = None
        
        # Get request path without query parameters
        path = request.url.path
        if request.url.query:
            path = f"{path}?{request.url.query}"
        
        try:
            # Execute request
            response = await call_next(request)
            
            # Calculate duration
            duration = (time.time() - start_time) * 1000
            
            # Create tracking
            tracking = APITracking(
                tracking_type=TrackingType.API_REQUEST,
                operation=f"{request.method} {request.url.path}",
                duration_ms=duration,
                status="success",
                endpoint=path,
                method=request.method,
                request_headers=dict(request.headers),
                request_body=request_body,
                response_status=response.status_code
            )
            
            # Save tracking asynchronously
            await self.tracking_service.save_tracking(tracking)
            
            return response
            
        except Exception as e:
            # Calculate duration even for errors
            duration = (time.time() - start_time) * 1000
            
            # Create error tracking
            tracking = APITracking(
                tracking_type=TrackingType.API_REQUEST,
                operation=f"{request.method} {request.url.path}",
                duration_ms=duration,
                status="error",
                error_message=str(e),
                endpoint=path,
                method=request.method,
                request_headers=dict(request.headers),
                request_body=request_body
            )
            
            # Save tracking asynchronously
            await self.tracking_service.save_tracking(tracking)
            
            raise
