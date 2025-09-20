from langchain_tavily import TavilySearch
from config.settings import settings


class SearchService:
    def __init__(self, api_key: str = settings.TAVILY_API_KEY, max_results: int = 3):
        self.api_key = api_key
        self.max_results = max_results
        self.client = TavilySearch(api_key=self.api_key)

    def search_activities(self, query: str) -> str:
        if not self.api_key:
            return "Error: TAVILY_API_KEY is not configured."

        results = self.client.run(f"{query} limit:{self.max_results}")
        activities = results["results"]

        if not activities:
            return f"No search results found for '{query}'."

        formatted = [
            f"- Source: {item.get('url', 'N/A')}\n  Snippet: {item.get('content', '')[:200]}..."
            for item in activities
            if isinstance(item, dict) 
        ]
        return "\n".join(formatted)
