"""
Router for monitoring endpoints
"""
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta
from typing import Optional
from src.services.tracking_service import TrackingService

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

async def get_tracking_service():
    tracking_service = TrackingService()
    await tracking_service.initialize()
    return tracking_service

@router.get("/metrics")
async def get_metrics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    tracking_service: TrackingService = Depends(get_tracking_service)
):
    """Get general system metrics"""
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=7)
    if not end_date:
        end_date = datetime.utcnow()

    return {
        "api_metrics": await tracking_service.get_api_metrics(start_date, end_date),
        "azure_metrics": await tracking_service.get_azure_metrics(start_date, end_date),
        "performance": await tracking_service.get_performance_metrics(start_date, end_date)
    }

@router.get("/azure-costs")
async def get_azure_costs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    tracking_service: TrackingService = Depends(get_tracking_service)
):
    """Get Azure OpenAI cost analysis"""
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    return await tracking_service.get_azure_metrics(start_date, end_date)

@router.get("/errors")
async def get_recent_errors(
    limit: int = Query(10, ge=1, le=100),
    tracking_service: TrackingService = Depends(get_tracking_service)
):
    """Get recent errors"""
    return await tracking_service.get_recent_errors(limit)
