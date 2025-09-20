from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api_routes import router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Activity Agent",
        description="An AI agent that suggests activities based on weather",
        version="1.0.0",
    )

    app.include_router(router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app

app = create_app()
