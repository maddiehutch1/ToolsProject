import json
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage

from backend.models import ChatRequest, HealthResponse
from backend.crisis import detect_crisis, CRISIS_RESPONSE
from backend.agent import run_agent_stream

load_dotenv()

app = FastAPI()

session_store: dict[str, list] = {}


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


@app.get("/health", response_model=HealthResponse)
def health():
    try:
        from backend.tools.rag_search import _vectorstore
        vector_status = "loaded" if _vectorstore else "not_loaded"
    except Exception:
        vector_status = "not_loaded"
    return {"status": "ok", "vector_store": vector_status}


@app.post("/chat")
async def chat(body: ChatRequest):
    if detect_crisis(body.message):
        async def crisis_stream():
            yield _sse({"type": "crisis", "content": CRISIS_RESPONSE})
            yield _sse({"type": "done"})
        return StreamingResponse(crisis_stream(), media_type="text/event-stream")

    history = session_store.setdefault(body.session_id, [])
    history.append(HumanMessage(content=body.message))

    async def event_stream():
        collected = []
        try:
            async for event in run_agent_stream(list(history)):
                collected.append(event)
                yield _sse(event)
        except Exception as e:
            yield _sse({"type": "error", "content": str(e)})
            yield _sse({"type": "done"})
            return

        full_text = "".join(
            e["content"] for e in collected if e.get("type") == "token"
        )
        history.append(AIMessage(content=full_text))

    return StreamingResponse(event_stream(), media_type="text/event-stream")


app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
