# Robotics Master

Central control system for distributed robotics projects (rover, robotic arm, DeskBot, FPV).

## Architecture

User input (text/voice) → Orchestrator → Ollama (LLM parser) → JSON command → ROS2 / MQTT → Robot

## Stack

- Ubuntu 24.04 host (Bosgame mini PC)
- ROS2 Humble in Docker (network_mode: host, ROS_DOMAIN_ID=42)
- Ollama (llama3.1:8b) for natural language to JSON command parsing
- FastAPI orchestrator with /command and /health endpoints
- Tailscale for remote access
- MQTT broker (planned, for Arduino/ESP32 nodes)

## Structure

- `ros2/` ROS2 Humble Docker setup, mounts a persistent workspace
- `orchestrator/` FastAPI service that parses natural language commands via Ollama
- `mosquitto/` MQTT broker config (planned)
- `data/` Logs, rosbags, telemetry (gitignored)

## Running

Start ROS2:

    cd ros2 && docker compose up -d

Start orchestrator:

    cd orchestrator && docker compose up -d --build

## Test the orchestrator

    curl -X POST http://localhost:8000/command \
      -H "Content-Type: application/json" \
      -d '{"text": "move the rover forward 2 meters"}'

Returns parsed JSON like:

    {"robot":"rover","action":"move","parameters":{"distance":2,"unit":"meters"}}

API docs at http://localhost:8000/docs

## Status

- [x] ROS2 Humble running in Docker
- [x] Ollama integration tested
- [x] Orchestrator parsing commands
- [x] Tailscale remote access
- [ ] Multi-machine ROS2 with Jetson
- [ ] MQTT broker
- [ ] Command routing to actual robots
- [ ] Web UI / dashboard
