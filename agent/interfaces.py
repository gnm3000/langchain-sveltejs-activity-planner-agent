from pydantic import BaseModel


class ResponseActivityModel(BaseModel):
    city: str
    greeting: str | None = None
    plan: str | None = None
    error: str | None = None
