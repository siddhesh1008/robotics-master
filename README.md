# Robotics Master

Central control system for distributed robotics projects (rover, robotic arm, DeskBot, FPV).

## Stack

- Ubuntu 24.04 host
- ROS2 Humble (Docker, network_mode host)
- Ollama (llama3.1:8b) for natural language command parsing
- MQTT (planned) for Arduino/ESP32 nodes
- FastAPI orchestrator (planned)

## Structure

- `ros2/` ROS2 Humble Docker setup
- `mosquitto/` MQTT broker config (planned)
- `orchestrator/` Master command service (planned)
- `data/` Logs, rosbags, telemetry (gitignored)

