from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
import json
import os

app = FastAPI(title="Robotics Master Orchestrator")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

PARSE_PROMPT = """Convert to JSON with fields: robot (string), action (string), parameters (object). Numbers must be numeric, not strings. Output raw JSON only.

Input: {user_input}
Output:"""


class CommandRequest(BaseModel):
    text: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/command")
async def command(req: CommandRequest):
    prompt = PARSE_PROMPT.format(user_input=req.text)

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
        )
        data = r.json()

    try:
        parsed = json.loads(data["response"])
    except json.JSONDecodeError:
        return {"error": "LLM returned invalid JSON", "raw": data["response"]}

    return {"input": req.text, "parsed": parsed}


@app.get("/")
async def root():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")
