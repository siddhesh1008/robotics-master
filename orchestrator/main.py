from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
import json
import os
import paho.mqtt.client as mqtt

app = FastAPI(title="Robotics Master Orchestrator")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
MQTT_HOST = os.getenv("MQTT_HOST", "host.docker.internal")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

PARSE_PROMPT = """Convert to JSON with fields: robot (string, lowercase, no spaces, use underscores), action (string), parameters (object). Numbers must be numeric, not strings. Output raw JSON only.

Input: {user_input}
Output:"""

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="orchestrator")
mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
mqtt_client.loop_start()


class CommandRequest(BaseModel):
    text: str


@app.get("/health")
async def health():
    return {"status": "ok", "mqtt_connected": mqtt_client.is_connected()}


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

    robot = parsed.get("robot", "unknown")
    topic = f"robots/{robot}/command"
    payload = json.dumps(parsed)

    result = mqtt_client.publish(topic, payload, qos=1)

    return {
        "input": req.text,
        "parsed": parsed,
        "published": {
            "topic": topic,
            "success": result.rc == mqtt.MQTT_ERR_SUCCESS,
        },
    }


@app.get("/")
async def root():
    return FileResponse("static/index.html")


app.mount("/static", StaticFiles(directory="static"), name="static")