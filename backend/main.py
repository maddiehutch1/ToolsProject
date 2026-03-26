import json
import logging
import logging.config
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage

from backend.models import ChatRequest, HealthResponse
from backend.crisis import detect_crisis, CRISIS_RESPONSE
from backend.agent import run_agent_stream

load_dotenv()

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
})

logger = logging.getLogger(__name__)

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
    logger.info("REQUEST session=%s message=%r", body.session_id, body.message[:120])

    if detect_crisis(body.message):
        logger.warning("CRISIS_DETECTED session=%s message=%r", body.session_id, body.message[:120])
        async def crisis_stream():
            yield _sse({"type": "crisis", "content": CRISIS_RESPONSE})
            yield _sse({"type": "done"})
        return StreamingResponse(crisis_stream(), media_type="text/event-stream")

    history = session_store.setdefault(body.session_id, [])
    history.append(HumanMessage(content=body.message))
    logger.info("SESSION session=%s history_length=%d", body.session_id, len(history))

    async def event_stream():
        collected = []
        try:
            async for event in run_agent_stream(list(history)):
                collected.append(event)
                yield _sse(event)
        except Exception as e:
            logger.error("STREAM_ERROR session=%s error=%s", body.session_id, e)
            yield _sse({"type": "error", "content": str(e)})
            yield _sse({"type": "done"})
            return

        full_text = "".join(
            e["content"] for e in collected if e.get("type") == "token"
        )
        logger.info("RESPONSE_COMPLETE session=%s tokens=%d", body.session_id, len(full_text))
        history.append(AIMessage(content=full_text))

    return StreamingResponse(event_stream(), media_type="text/event-stream")


app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
