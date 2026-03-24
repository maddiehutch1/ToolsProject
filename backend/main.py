from fastapi import FastAPI
from backend.models import HealthResponse

app = FastAPI()


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}
