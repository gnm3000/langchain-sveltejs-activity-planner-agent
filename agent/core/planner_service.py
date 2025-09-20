from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from core.weather_service import WeatherService
from core.search_service import SearchService
from config.settings import settings

class PlannerService:
    def __init__(self, weather: WeatherService, search: SearchService):
        self.weather = weather
        self.search = search
        self.agent_executor = self._initialize_agent()

    def _initialize_agent(self) -> AgentExecutor:
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=settings.OPENAI_API_KEY,
        )

        # Wrapping functions as LangChain Tool objects
        tools = [
            Tool(
                name="WeatherTool",
                func=self.weather.get_weather,
                description="Returns the current weather for a given city."
            ),
            Tool(
                name="ActivitySearchTool",
                func=self.search.search_activities,
                description="Search for activities and official links for a given query."
            )
        ]

        # Load system prompt
        with open("prompts/system_prompt.md", encoding="utf-8") as f:
            system_message = f.read()

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        return AgentExecutor(
            agent=create_openai_tools_agent(llm, tools, prompt),
            tools=tools,
            verbose=False,
        )

    def generate_plan(self, city: str) -> str:
        agent_input = {"input": f"Provide activity suggestions for {city}."}
        response = self.agent_executor.invoke(agent_input)
        return response.get("output", "No output generated.")
