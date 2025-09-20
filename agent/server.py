"""FastAPI server powering the SmartCity activity planner."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, cast

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from interfaces import ResponseActivityModel
load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MAX_CONTENT_SNIPPET_LENGTH = 200

agent_executor: AgentExecutor | None = None
app_initialized_successfully = False


@tool
def get_weather(city: str) -> str:
    """Return the current weather in the given city using OpenWeatherMap."""

    if not OPENWEATHERMAP_API_KEY:
        return "Error: OPENWEATHERMAP_API_KEY is not configured."

    url = (
        "http://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
    )
    response = requests.get(url, timeout=10)
    if response.status_code != 200:
        return f"Error: {response.status_code}, {response.text}"

    data = response.json()
    weather = data["weather"][0]["description"]
    temperature = data["main"]["temp"]
    return f"The current weather in {city} is {weather} with a \
        temperature of {temperature}\u00b0C."


@tool
def search_activity_links_tavily(activity_query: str) -> str:
    """Search for activity links using Tavily."""

    if not TAVILY_API_KEY:
        return "Error: TAVILY_API_KEY is not configured."

    try:
        search_tool = TavilySearchResults(max_results=3, api_key=TAVILY_API_KEY)
        raw_results = search_tool.invoke({"query": activity_query})
        results = cast(List[Dict[str, Any]], raw_results) if raw_results else []
        if not results:
            return f"No search results found for '{activity_query}' using Tavily."

        formatted_results: List[str] = []
        for res in results:
            url = res.get("url", "N/A URL")
            content_snippet = res.get("content", "N/A Content")
            if (
                isinstance(content_snippet, str)
                and len(content_snippet) > MAX_CONTENT_SNIPPET_LENGTH
            ):
                content_snippet = (
                    content_snippet[: MAX_CONTENT_SNIPPET_LENGTH - 3] + "..."
                )
            formatted_results.append(f"- Source: {url}\n  Snippet: {content_snippet}")

        return f"Tavily search results for '{activity_query}':\n" + "\n".join(
            formatted_results
        )
    except Exception as exc:  # pragma: no cover - safeguard against Tavily failures
        return (
            "Error: An unexpected error occurred during Tavily search for "
            f"'{activity_query}': {exc}"
        )


async def lifespan_context_manager(app_instance: FastAPI):
    """Manage agent lifecycle while the FastAPI app is running."""

    global agent_executor, app_initialized_successfully

    logger.info("Starting up activity planner agent")

    try:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured.")

        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            openai_api_key=OPENAI_API_KEY,
        )
        tools = [get_weather, search_activity_links_tavily]
        # read the file in prompts/system_message.txt
        with open("prompts/system_prompt.md", "r", encoding="utf-8") as f:
            system_message = f.read()

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        agent = create_openai_tools_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            handle_parsing_errors=(
                "An error occurred while parsing the \
                    agent's output. Please check the format \
                        and try again."
            ),
        )
        app_initialized_successfully = True
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Error during app initialization: %s", exc)
        app_initialized_successfully = False

    if app_initialized_successfully and agent_executor is not None:
        app_instance.state.agent_executor = agent_executor
        logger.info("App initialized successfully")
    else:
        app_instance.state.agent_executor = None
        logger.error(
            "App failed to initialize properly. \
                Endpoints will return an error if called."
        )

    yield
    logger.info("Shutting down activity planner agent")


app = FastAPI(
    title="Activity Agent",
    description="An AI agent that suggests activities based on the weather forecast.",
    version="1.0.0",
    lifespan=lifespan_context_manager,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root() -> Dict[str, str]:
    """Return a simple health payload for smoke testing."""

    return {"Hello": "World"}


@app.get("/get-activity", response_model=ResponseActivityModel)
async def get_activity(city: str) -> ResponseActivityModel:
    """Execute the planner agent to build an activity plan for the given city."""

    if not app_initialized_successfully or agent_executor is None:
        raise HTTPException(
            status_code=503,
            detail="Service Unavailable: \
                The planner agent is not initialized. \
                    Check server logs for errors.",
        )

    if not city.strip():
        raise HTTPException(status_code=400, detail="City name cannot be empty.")

    logger.info("Received request for city: %s", city)
    try:
        agent_input = {"input": f"Provide activity suggestions for {city}."}
        response = agent_executor.invoke(agent_input)
        output = response.get("output")
        if output:
            friendly_greeting = (
                f"Hola, soy tu asesor de actividades. Aqui tienes un plan para {city}:"
            )
            logger.info("Sending plan for city: %s", city)
            return ResponseActivityModel(
                city=city, greeting=friendly_greeting, plan=output
            )

        error_message = (
            "Agent executed but did not produce a standard output. Raw response: "
            + str(response)
        )
        logger.warning(error_message)
        return ResponseActivityModel(city=city, error=error_message)

    except Exception as exc:  # pragma: no cover - defensive logging
        logger.exception("Error during agent execution for city '%s'", city)
        raise HTTPException(
            status_code=500,
            detail=(
                "An unexpected error occurred while processing your request for "
                f"{city}: {exc}"
            ),
        )
