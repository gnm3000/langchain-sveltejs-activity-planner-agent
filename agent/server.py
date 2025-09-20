# FAST API python server 
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()
import os
from fastapi import FastAPI, HTTPException, Query


OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

from langchain_openai import ChatOpenAI

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
#result=llm.invoke("Hello world")
#print("openai llm",result)

tools = []
from langchain_core.tools import tool
@tool
def get_weather(city: str) -> str:
    """Get the current weather in a given city."""
    import requests
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
    response = requests.get(url)
    if response.status_code != 200:
        return f"Error: {response.status_code}, {response.text}"
    data = response.json()
    weather = data["weather"][0]["description"]
    temperature = data["main"]["temp"]
    return f"The current weather in {city} is {weather} with a temperature of {temperature}°C."


from langchain_community.tools.tavily_search import TavilySearchResults
@tool
def search_activity_links_tavily(activity_query: str) -> str:
    """Search for activity links using Tavily."""
    try:
        search_tool = TavilySearchResults(max_results=3, api_key=TAVILY_API_KEY) # Using API key directly
        results = search_tool.invoke({"query": activity_query})
        
        if not results:
            return f"No search results found for '{activity_query}' using Tavily."

        formatted_results = []
        for res in results:
            url = res.get('url', 'N/A URL')
            content_snippet = res.get('content', 'N/A Content')
            if len(content_snippet) > 200: content_snippet = content_snippet[:197] + "..."
            formatted_results.append(f"- Source: {url}\n  Snippet: {content_snippet}")
        
        return f"Tavily search results for '{activity_query}':\n" + "\n".join(formatted_results)
    except Exception as e:
        return f"Error: An unexpected error occurred during Tavily search for '{activity_query}': {e}"



async def lifespan_context_manager(app_instance: FastAPI):
    print("Starting up...")
    global agent_executor, app_initialized_successfully

    try:
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=OPENAI_API_KEY)
        tools = [get_weather, search_activity_links_tavily]
        system_message = """
                You are a SmartCity Activity Planner. Your goal is to help users plan activities in a specified city.
                Your answer must be in spanish language.
                Follow these steps:
                1.  When a user provides a city name, first use the `get_current_weather` tool to fetch the current weather conditions for that city.
                2.  Based on the weather conditions, suggest 3 to 5 appropriate activities.
                3.  For each suggested activity, use the `search_activity_links_tavily` tool to find relevant information or official links. Query should be specific like "[Activity Name] [City] official website".
                4.  Compile all the information (weather, 3-5 activity suggestions with their corresponding links/info from Tavily) into a single, concise, and user-friendly response.
                5.  If a tool fails or cannot find specific information, clearly state that in your response for that part, but try to complete the rest of the request.
                6.  Do not make up weather information or links. Rely solely on the output from the tools.
                7.  Present the final plan directly to the user.
                8.  If the city name is ambiguous or missing, ask the user for clarification.
                """
        prompt = ChatPromptTemplate.from_messages(
                    [
                        ("system", system_message),
                        ("human", "{input}"),
                        MessagesPlaceholder(variable_name="agent_scratchpad"),
                    ]
                )

        # --- Agent and Executor ---
        agent = create_openai_tools_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True, # Good for debugging, set to False in production
            handle_parsing_errors="An error occurred while parsing the agent's output. Please check the format and try again."
        )
        app_initialized_successfully = True
    except Exception as e:
        print(f"Error during app initialization: {e}")
        app_initialized_successfully = False
    if app_initialized_successfully:
        app_instance.state.agent_executor = agent_executor
        print("App initialized successfully.")
        
    else:
        app_instance.state.agent_executor = None
        print("App failed to initialize properly. Endpoints will return an error if called.")
    yield
    print("Shutting down...")

app = FastAPI(
    title="Activity Agent",
    description="An AI agent that suggests activities based on the weather forecast.",
    version="1.0.0",
    lifespan=lifespan_context_manager
)
from fastapi.middleware.cors import CORSMiddleware

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite cualquier origen. Puedes restringirlo a ["https://tu-dominio.com"]
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos: GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Permite todos los headers
)
@app.get("/")
def read_root():
    return {"Hello": "World"}
## fast api endpoint ###


class ResponseActivityModel(BaseModel):
    city: str
    greeting: str | None = None
    plan: str | None = None
    error: str | None = None
    
@app.get("/get-activity", response_model=ResponseActivityModel)
async def get_activity(city: str):
    if not app_initialized_successfully or agent_executor is None:
        raise HTTPException(status_code=503, detail="Service Unavailable: The planner agent is not initialized. Check server logs for errors.")

    if not city.strip():
        raise HTTPException(status_code=400, detail="City name cannot be empty.")
    try:
        print(f"Received request for city: {city}")
        # Construct the input for the agent, matching the prompt's "{input}" variable
        agent_input = {"input": f"Provide activity suggestions for {city}."}
        
        response = agent_executor.invoke(agent_input)
        
        output = response.get("output")
        if output:
            friendly_greeting = f"Hello from your Activties Advisor! Here's a plan for {city}:"
            print(f"AGENT_UPGRADE_V2: Sending greeting: '{friendly_greeting}")
            return ResponseActivityModel(city=city, greeting=friendly_greeting, plan=output)
        else:
            error_message = "Agent executed but did not produce a standard output. Raw response: " + str(response)
            print(f"Warning: {error_message}")
            return ResponseActivityModel(city=city, error=error_message)

    except Exception as e:
        print(f"Error during agent execution for city '{city}': {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while processing your request for {city}: {str(e)}")

    

