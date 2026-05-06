# CRCS — Centralized Robotic Control System

> Talk to your robots. CRCS handles the rest.

CRCS is a framework that turns one mini PC into a brain for a fleet of robots. You speak or type a command in plain English, a local AI model parses it into structured instructions, and CRCS routes those instructions to the right robot over a shared message bus. Robots report their state back, and you can watch them move in real-time on a live web view.

Built in public as a learning project. Not yet stable for general use, but the foundation works end-to-end.

## Architecture

```
User input (text/voice) → Web UI / API → Orchestrator → Ollama (LLM parser)
                              ↑                  ↓
                              |          Publish JSON to MQTT
                              |                  ↓
                              |           Robot subscribes
                              |                  ↓
                              |           Robot executes
                              |                  ↓
                              |     Robot publishes status + position
                              |                  ↓
                              └──── Live update via WebSocket
```

## Stack

- Ubuntu 24.04 host
- ROS2 Humble in Docker (`network_mode: host`, `ROS_DOMAIN_ID=42`)
- Ollama running `llama3.1:8b` for natural language to JSON command parsing
- FastAPI orchestrator with web UI, REST API, and WebSocket bridge
- Mosquitto MQTT broker as the message bus
- Tailscale for remote access

## Repository structure

- `ros2/` ROS2 Humble Docker setup, mounts a persistent workspace
- `orchestrator/` FastAPI service. Parses commands via Ollama, publishes to MQTT, subscribes to robot status, exposes WebSocket for live UI updates
- `mosquitto/` MQTT broker config and persistence
- `examples/fake_robots/` Simulated robots for testing CRCS without real hardware
- `data/` Logs, rosbags, telemetry (gitignored)

## Running

Start ROS2:
```
cd ros2 && docker compose up -d
```

Start MQTT broker:
```
cd mosquitto && docker compose up -d
```

Start orchestrator:
```
cd orchestrator && docker compose up -d --build
```

Start a fake rover (in a separate terminal):
```
cd examples/fake_robots
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python fake_rover.py
```

## Using it

**Main command UI**
```
http://localhost:8000/
```

**Live rover view (2D top-down)**
```
http://localhost:8000/rover-2d
```

Watch the rover move in real-time as commands are sent. Position, heading, and state update via WebSocket.

**Or use the API directly**
```
curl -X POST http://localhost:8000/command \
  -H "Content-Type: application/json" \
  -d '{"text": "move the rover forward 2 meters"}'
```

Returns:
```json
{
  "input": "move the rover forward 2 meters",
  "parsed": {"robot": "rover", "action": "move", "parameters": {"distance": 2}},
  "published": {"topic": "robots/rover/command", "success": true}
}
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main command UI |
| GET | `/rover-2d` | Live 2D rover visualization |
| POST | `/command` | Parse and dispatch a natural-language command |
| GET | `/robots` | Latest known state of every robot |
| GET | `/robots/<name>` | Latest known state of one robot |
| GET | `/health` | Service status (MQTT connection, robots seen, WS clients) |
| WS | `/ws` | Live status stream (snapshot on connect, then push on every robot update) |

## MQTT topics

| Direction | Topic | Description |
|-----------|-------|-------------|
| Master → Robot | `robots/<name>/command` | Structured JSON command |
| Robot → Master | `robots/<name>/status` | State, position, telemetry |

Subscribe to all robot traffic:
```
mosquitto_sub -h <master-ip> -t "robots/#" -v
```

## Status

- [x] ROS2 Humble running in Docker
- [x] Ollama integration tested
- [x] Orchestrator parsing commands
- [x] Web UI for sending commands
- [x] Tailscale remote access
- [x] MQTT broker live
- [x] Orchestrator publishing parsed commands to MQTT topics
- [x] Robot name validation (rejects unknown robots before publishing)
- [x] Fake rover with position tracking (x, y, heading)
- [x] Orchestrator subscribes to robot status
- [x] WebSocket bridge for live browser updates
- [x] 2D live rover view with smooth animation
- [ ] Fake arm and fake bot examples
- [ ] Multi-machine ROS2 with Jetson
- [ ] MQTT-to-ROS2 bridge
- [ ] Voice input
- [ ] 3D showcase view

## Built in public

CRCS is a personal project I'm developing openly. Code is MIT licensed, ideas and feedback welcome via Issues, but no support guarantees yet. Once a real robot is connected end-to-end and the system has been stable for a few weeks, I'll start treating it as a real open-source project with proper contribution guidelines.

For a non-technical overview, see [OVERVIEW.md](OVERVIEW.md).

## License

MIT