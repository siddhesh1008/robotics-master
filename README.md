# CRCS — Centralized Robotic Control System

> Talk to your robots. CRCS handles the rest.

CRCS is a framework that turns one mini PC into a brain for a fleet of robots. You speak or type a command in plain English, a local AI model parses it into structured instructions, and CRCS routes those instructions to the right robot over a shared message bus.

Built in public as a learning project. Not yet stable for general use, but the foundation works.

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

- Ubuntu 24.04 host
- ROS2 Humble in Docker (`network_mode: host`, `ROS_DOMAIN_ID=42`)
- Ollama running `llama3.1:8b` for natural language to JSON command parsing
- FastAPI orchestrator with web UI, `/command`, and `/health` endpoints
- Mosquitto MQTT broker for Arduino/ESP32 nodes
- Tailscale for remote access

## Repository structure

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
- [ ] First real robot connected end-to-end

## Built in public

CRCS is a personal project I'm developing openly. Code is MIT licensed, ideas and feedback welcome via Issues, but no support guarantees yet. Once a real robot is connected end-to-end and the system has been stable for a few weeks, I'll start treating it as a real open-source project with proper contribution guidelines.

For a non-technical overview of what CRCS does and why, see [OVERVIEW.md](OVERVIEW.md).

## License

MIT