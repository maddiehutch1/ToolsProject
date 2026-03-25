from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: str


class HealthResponse(BaseModel):
    status: str
    vector_store: str = "not_loaded"
