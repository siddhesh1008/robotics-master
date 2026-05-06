from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import httpx
import json
import os
import asyncio
import paho.mqtt.client as mqtt
from typing import Dict, Any, Set

app = FastAPI(title="CRCS Orchestrator")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
MQTT_HOST = os.getenv("MQTT_HOST", "host.docker.internal")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

KNOWN_ROBOTS = ["rover", "arm", "bot"]

PARSE_PROMPT = """You are a command parser for a robot fleet. Convert the user input into JSON.

Known robots: {robots}

Rules:
- "robot" must be exactly one of the known robot names. If the user says "the rover", use "rover". If they say "robotic arm" or "the arm", use "arm". If they say "companion bot" or "deskbot", use "bot".
- "action" should be a single lowercase verb (move, rotate, stop, pick, place, smile, wave, reset, etc.)
- "parameters" is an object with relevant numeric or string fields.
- For rotation, use the key "angle" for the amount in degrees.
- For movement, use the key "distance" for the amount in meters.
- Numbers must be numeric, not strings.
- Output raw JSON only.

Input: {user_input}
Output:"""


class CommandRequest(BaseModel):
    text: str


# In-memory store of latest robot states. Key = robot name.
robot_states: Dict[str, Dict[str, Any]] = {}

# Active WebSocket connections
ws_clients: Set[WebSocket] = set()

# Reference to the main asyncio loop (set at startup)
main_loop: asyncio.AbstractEventLoop = None


async def broadcast_to_clients(message: dict):
    """Send a message to every connected WebSocket client."""
    if not ws_clients:
        return
    payload = json.dumps(message)
    dead = []
    for ws in ws_clients:
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        ws_clients.discard(ws)


# MQTT setup
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="orchestrator")


def on_connect(client, userdata, flags, rc, properties=None):
    print(f"[orchestrator] MQTT connected (rc={rc})")
    client.subscribe("robots/+/status", qos=1)
    print("[orchestrator] subscribed to robots/+/status")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        print(f"[orchestrator] invalid JSON on {msg.topic}")
        return

    parts = msg.topic.split("/")
    if len(parts) != 3:
        return
    robot_name = parts[1]

    robot_states[robot_name] = payload
    state = payload.get("state", "?")
    pos = payload.get("position", {})
    print(f"[orchestrator] {robot_name} -> {state} @ {pos}")

    # Push to all connected browsers via WebSocket
    if main_loop is not None:
        asyncio.run_coroutine_threadsafe(
            broadcast_to_clients({"type": "status", "robot": robot_name, "data": payload}),
            main_loop,
        )


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


@app.on_event("startup")
async def startup():
    global main_loop
    main_loop = asyncio.get_event_loop()
    mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
    mqtt_client.loop_start()


@app.on_event("shutdown")
async def shutdown():
    mqtt_client.loop_stop()
    mqtt_client.disconnect()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "mqtt_connected": mqtt_client.is_connected(),
        "robots_seen": list(robot_states.keys()),
        "ws_clients": len(ws_clients),
    }


@app.get("/robots")
async def robots():
    return robot_states


@app.get("/robots/{name}")
async def robot(name: str):
    if name not in robot_states:
        return {"error": f"No status received from '{name}' yet"}
    return robot_states[name]


@app.post("/command")
async def command(req: CommandRequest):
    prompt = PARSE_PROMPT.format(
        robots=", ".join(KNOWN_ROBOTS),
        user_input=req.text,
    )

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

    if robot not in KNOWN_ROBOTS:
        return {
            "input": req.text,
            "parsed": parsed,
            "error": f"Unknown robot '{robot}'. Known robots: {KNOWN_ROBOTS}",
            "published": None,
        }

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


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    ws_clients.add(ws)
    print(f"[orchestrator] WS client connected (total: {len(ws_clients)})")

    # Send initial snapshot of all robot states
    await ws.send_text(json.dumps({"type": "snapshot", "data": robot_states}))

    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_clients.discard(ws)
        print(f"[orchestrator] WS client disconnected (total: {len(ws_clients)})")
    except Exception as e:
        ws_clients.discard(ws)
        print(f"[orchestrator] WS error: {e}")


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/rover-2d")
async def rover_2d_view():
    return FileResponse("static/rover_2d.html")


app.mount("/static", StaticFiles(directory="static"), name="static")