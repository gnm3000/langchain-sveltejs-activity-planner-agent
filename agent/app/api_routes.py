from fastapi import APIRouter, HTTPException
from interfaces import ResponseActivityModel
from core.planner_service import PlannerService
from core.weather_service import WeatherService
from core.search_service import SearchService
from config.settings import settings



router = APIRouter()
planner = PlannerService(WeatherService(api_key=settings.OPENWEATHERMAP_API_KEY), SearchService(api_key=settings.TAVILY_API_KEY))

@router.get("/get-activity", response_model=ResponseActivityModel)
async def get_activity(city: str) -> ResponseActivityModel:
    if not city.strip():
        raise HTTPException(status_code=400, detail="City name cannot be empty.")

    output = planner.generate_plan(city)
    return ResponseActivityModel(city=city, greeting=f"Plan for {city}", plan=output)
