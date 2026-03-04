import os
import json
import asyncio
try:
    import chainlit as cl
    from chainlit.utils import mount_chainlit
    CHAINLIT_AVAILABLE = True
except Exception:
    # Chainlit is optional for running the FastAPI app. If it's not installed
    # the app will still start; Chainlit-specific features will be disabled.
    cl = None
    mount_chainlit = None
    CHAINLIT_AVAILABLE = False

from fastapi import FastAPI, UploadFile, File, HTTPException

# Use full package import
try:
    from app.engine import get_streaming_rag_response
    ENGINE_AVAILABLE = True
except Exception as e:
    # Engine or its dependencies might be missing in this environment.
    ENGINE_AVAILABLE = False
    async def get_streaming_rag_response(*args, **kwargs):
        raise RuntimeError(f"Engine not available: {e}")

app = FastAPI()

# Redis connection (optional)
try:
    import redis.asyncio as redis
    redis_client = redis.from_url("redis://redis:6379", decode_responses=True)
    REDIS_AVAILABLE = True
except Exception:
    redis = None
    redis_client = None
    REDIS_AVAILABLE = False

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/ingest")
async def ingest_file(file: UploadFile = File(...)):
    content = await file.read()
    task = {
        "filename": file.filename,
        "content": content.decode("utf-8")
    }
    if not REDIS_AVAILABLE or redis_client is None:
        raise HTTPException(status_code=503, detail="Redis is not available. Install 'redis' package or run in an environment with Redis client available.")

    await redis_client.lpush("ingest_queue", json.dumps(task))
    return {"message": f"Successfully queued {file.filename}"}

# --- Chainlit Logic ---

if CHAINLIT_AVAILABLE:
    @cl.on_chat_start
    async def start():
        cl.user_session.set("history", [])
        await cl.Message(content="RAG System Ready.").send()

    @cl.on_message
    async def main(message: cl.Message):
        msg = cl.Message(content="")
        async for token in get_streaming_rag_response(message.content):
            await msg.stream_token(token)
        await msg.send()
else:
    # Provide a minimal fallback so importing this module still works when
    # Chainlit isn't installed. This keeps the FastAPI endpoints functioning.
    async def start():
        return None

    async def main(message):
        # No-op fallback
        return None

# --- Mounting Logic (THE FIX) ---

# We only want to mount if this is the FastAPI process starting up.
# Chainlit sets an environment variable when it's the one doing the loading.
if CHAINLIT_AVAILABLE and not os.environ.get("CHAINLIT_RUN"):
    # Prevent mount_chainlit from re-importing this module and causing a
    # recursive loop. Set the environment variable so subsequent imports by
    # chainlit's loader won't try to mount again.
    os.environ["CHAINLIT_RUN"] = "1"
    current_file_path = os.path.abspath(__file__)
    mount_chainlit(app, target=current_file_path, path="/")