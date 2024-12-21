"""
Aspect for tracking Azure OpenAI API calls
"""
import functools
import time
from typing import Callable, Any, Dict, Union
from src.models.tracking import APITracking, TrackingType
from src.services.tracking_service import TrackingService
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI

def calculate_azure_cost(model: str, tokens_used: int = 0) -> float:
    """
    Calculate estimated cost based on Azure OpenAI pricing
    https://azure.microsoft.com/en-us/pricing/details/cognitive-services/openai-service/
    """
    # Pricing per 1K tokens (USD)
    pricing = {
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-4-32k": {"prompt": 0.06, "completion": 0.12},
        "gpt-35-turbo": {"prompt": 0.0015, "completion": 0.002},
        "text-embedding-ada-002": {"prompt": 0.0001, "completion": 0.0}
    }
    
    model_pricing = pricing.get(model.lower(), {"prompt": 0.0, "completion": 0.0})
    total_cost = (tokens_used / 1000) * (model_pricing["prompt"] + model_pricing["completion"])
    
    return total_cost

def track_azure_call(operation: str, model: str):
    """Decorator for tracking Azure OpenAI API calls"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            tracking_service = TrackingService()
            await tracking_service.initialize()
            
            try:
                # Execute the original function
                result = await func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                
                # Initialize tracking data
                tokens_used = 0
                metadata = {}
                
                # Handle different return types
                if isinstance(result, (AzureOpenAIEmbeddings, AzureChatOpenAI)):
                    metadata = {"model_type": result.__class__.__name__}
                else:
                    # Assume it's a response dictionary
                    usage = result.get("usage", {})
                    tokens_used = usage.get("total_tokens", 0)
                    metadata = {"response": result}
                
                # Calculate cost
                cost = calculate_azure_cost(model, tokens_used)
                
                # Create tracking record
                tracking = APITracking(
                    tracking_type=TrackingType.AZURE_OPENAI,
                    operation=operation,
                    model=model,
                    status="success",
                    duration_ms=duration,
                    estimated_cost=cost,
                    prompt_tokens=0,  # Will be updated when actually used
                    completion_tokens=0,  # Will be updated when actually used
                    metadata=metadata
                )
                
                # Save tracking asynchronously
                await tracking_service.save_tracking(tracking)
                
                return result
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                
                # Create error tracking record
                tracking = APITracking(
                    tracking_type=TrackingType.AZURE_OPENAI,
                    operation=operation,
                    model=model,
                    status="error",
                    duration_ms=duration,
                    error_message=str(e),
                    metadata={"error": str(e)}
                )
                
                # Save tracking asynchronously
                await tracking_service.save_tracking(tracking)
                
                # Re-raise the exception
                raise
                
        return wrapper
    return decorator
