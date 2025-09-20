import requests
from config.settings import settings


class WeatherService:
    """Service to fetch weather information using OpenWeatherMap API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"

    def get_weather(self, city: str) -> str:
        """Return the current weather in the given city."""
        if not self.api_key:
            return "Error: OPENWEATHERMAP_API_KEY is not configured."

        url = f"{self.base_url}?q={city}&appid={self.api_key}&units=metric"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return f"Error: {response.status_code}, {response.text}"

        data = response.json()
        weather = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        return (
            f"The current weather in {city} is {weather} with a "
            f"temperature of {temperature}\u00b0C."
        )