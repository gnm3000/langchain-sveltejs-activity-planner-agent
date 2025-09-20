import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENWEATHERMAP_API_KEY: str = os.getenv("OPENWEATHERMAP_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MAX_CONTENT_SNIPPET_LENGTH: int = 200
settings = Settings()