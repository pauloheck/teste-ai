"""
Service for handling tracking operations
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from src.models.tracking import APITracking, TrackingType
from src.core.database import get_collection

class TrackingService:
    _instance: Optional['TrackingService'] = None
    _collection: Optional[AsyncIOMotorCollection] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def initialize(self):
        """Initialize the tracking service with database collection"""
        if self._collection is None:
            self._collection = await get_collection("tracking")
            # Create indexes
            await self._collection.create_index("tracking_type")
            await self._collection.create_index("timestamp")
            await self._collection.create_index("operation")
            await self._collection.create_index([("model", 1), ("operation", 1)])
    
    async def save_tracking(self, tracking: APITracking) -> str:
        """Saves a tracking record"""
        if self._collection is None:
            await self.initialize()
        result = await self._collection.insert_one(tracking.dict(by_alias=True))
        return str(result.inserted_id)

    async def get_api_metrics(self, start_date: datetime, end_date: datetime):
        """Gets API metrics"""
        if self._collection is None:
            await self.initialize()
        pipeline = [
            {
                "$match": {
                    "tracking_type": TrackingType.API_REQUEST,
                    "timestamp": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$endpoint",
                    "total_requests": {"$sum": 1},
                    "avg_duration": {"$avg": "$duration_ms"},
                    "success_rate": {
                        "$avg": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}
                    },
                    "error_count": {
                        "$sum": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}
                    }
                }
            }
        ]
        return await self._collection.aggregate(pipeline).to_list(None)

    async def get_azure_metrics(self, start_date: datetime, end_date: datetime):
        """Gets Azure OpenAI metrics"""
        if self._collection is None:
            await self.initialize()
        pipeline = [
            {
                "$match": {
                    "tracking_type": TrackingType.AZURE_OPENAI,
                    "timestamp": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "model": "$model",
                        "operation": "$operation"
                    },
                    "total_calls": {"$sum": 1},
                    "avg_duration": {"$avg": "$duration_ms"},
                    "total_cost": {"$sum": "$estimated_cost"},
                    "total_tokens": {
                        "$sum": {
                            "$add": ["$prompt_tokens", "$completion_tokens"]
                        }
                    },
                    "success_rate": {
                        "$avg": {"$cond": [{"$eq": ["$status", "success"]}, 1, 0]}
                    }
                }
            }
        ]
        return await self._collection.aggregate(pipeline).to_list(None)

    async def get_performance_metrics(self, start_date: datetime, end_date: datetime):
        """Gets general performance metrics"""
        if self._collection is None:
            await self.initialize()
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$tracking_type",
                    "total_requests": {"$sum": 1},
                    "avg_duration": {"$avg": "$duration_ms"},
                    "max_duration": {"$max": "$duration_ms"},
                    "min_duration": {"$min": "$duration_ms"},
                    "error_rate": {
                        "$avg": {"$cond": [{"$eq": ["$status", "error"]}, 1, 0]}
                    }
                }
            }
        ]
        return await self._collection.aggregate(pipeline).to_list(None)

    async def get_recent_errors(self, limit: int = 10):
        """Gets most recent errors"""
        if self._collection is None:
            await self.initialize()
        cursor = self._collection.find(
            {"status": "error"},
            sort=[("timestamp", -1)]
        ).limit(limit)
        return await cursor.to_list(None)
