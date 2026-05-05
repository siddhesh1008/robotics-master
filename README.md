# Robotics Master

Central control system for distributed robotics projects. One mini PC acts as the brain, parses natural language commands via a local LLM, and dispatches structured instructions to robots over MQTT and ROS2.

## Architecture

```
User input (text/voice) → Web UI / API → Orchestrator → Ollama (LLM parser)
                                                   ↓
                                           Publish JSON
                                           ↙          ↘
                                       MQTT          ROS2
                                         ↓             ↓
                                   Arduino/ESP32   Jetson/Pi
```

## Stack

- Ubuntu 24.04 host (Bosgame mini PC, Ryzen 5 6600H, 24GB RAM)
- ROS2 Humble in Docker (network_mode: host, ROS_DOMAIN_ID=42)
- Ollama running llama3.1:8b for natural language to JSON command parsing
- FastAPI orchestrator with web UI, /command, and /health endpoints
- Mosquitto MQTT broker for Arduino/ESP32 nodes
- Tailscale for remote access

## Structure

- `ros2/` ROS2 Humble Docker setup, mounts a persistent workspace
- `orchestrator/` FastAPI service, web UI, parses commands via Ollama, publishes to MQTT
- `mosquitto/` MQTT broker config and persistence
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

## Using it

Open the web UI at `http://localhost:8000/` (or `http://<tailscale-ip>:8000/` from your phone).

Or use the API directly:
```
curl -X POST http://localhost:8000/command \
  -H "Content-Type: application/json" \
  -d '{"text": "move the rover forward 2 meters"}'
```

Returns:
```json
{
  "input": "move the rover forward 2 meters",
  "parsed": {"robot": "rover", "action": "move", "parameters": {"distance": 2, "unit": "meters"}},
  "published": {"topic": "robots/rover/command", "success": true}
}
```

## Subscribing to commands (from any robot)

Listen to all robot commands:
```
mosquitto_sub -h <master-ip> -t "robots/#" -v
```

Listen to a specific robot:
```
mosquitto_sub -h <master-ip> -t "robots/rover/command" -v
```

## Status

- [x] ROS2 Humble running in Docker
- [x] Ollama integration tested
- [x] Orchestrator parsing commands
- [x] Web UI for sending commands
- [x] Tailscale remote access
- [x] MQTT broker live
- [x] Orchestrator publishing parsed commands to MQTT topics
- [ ] Multi-machine ROS2 with Jetson
- [ ] MQTT-to-ROS2 bridge
- [ ] Voice input
- [ ] Robot acknowledgments and telemetry back to master