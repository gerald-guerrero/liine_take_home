"""
FastAPI app for checking opening times for restaurants.

Simple REST API that tells you which restaurants are open based on user date time input.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel

from .services import RestaurantService


# Initialize restaurant service
restaurant_service = RestaurantService()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle application startup and shutdown."""
    # Startup
    csv_file_path = os.getenv("RESTAURANTS_CSV_FILE", "restaurants.csv")
    
    if os.path.exists(csv_file_path):
        try:
            restaurant_service.load_restaurants_from_csv(csv_file_path)
            print(f"Successfully loaded restaurant data from {csv_file_path}")
        except Exception as exc:
            print(f"Warning: Could not load restaurant data: {exc}")
    else:
        print(f"Warning: Restaurant CSV file not found at {csv_file_path}")
    
    yield
    
    # Shutdown (if needed)
    print("Application shutting down")


# API response models
class RestaurantsResponse(BaseModel):
    """List of restaurants."""
    restaurants: list[str]


class CountResponse(BaseModel):
    """Simple count numberto keep track of restaurants."""
    count: int


class HealthResponse(BaseModel):
    """Health check info for current API status."""
    status: str
    message: str


# Initialize FastAPI app
app = FastAPI(
    title="Restaurant Hours API",
    description="API for querying restaurant opening hours",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Simple health check to determine if API is working"""
    return HealthResponse(
        status="healthy",
        message="Restaurant Hours API is running"
    )


@app.get("/restaurants/open", response_model=RestaurantsResponse)
async def get_open_restaurants(
    datetime_param: str = Query(..., alias="datetime")
) -> RestaurantsResponse:
    """
    Find restaurants that are open at the time given by user input.
    
    Pass in a datetime such as "Mon 11:30 am", and get back a 
    list of open restaurants 
    """
    if not restaurant_service.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Restaurant data not loaded"
        )
    
    try:
        open_restaurants = restaurant_service.find_open_restaurants(datetime_param)
        return RestaurantsResponse(restaurants=open_restaurants)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid datetime format: {str(exc)}"
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(exc)}"
        ) from exc


@app.get("/restaurants/count", response_model=CountResponse)
async def get_restaurant_count() -> CountResponse:
    """
    Returns total number of loaded restaurants
    """
    if not restaurant_service.is_loaded():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Restaurant data not loaded"
        )
    
    count = restaurant_service.get_restaurant_count()
    return CountResponse(count=count)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 