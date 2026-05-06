# Fake Robots

Simulated robots for testing CRCS without real hardware.

Each fake robot connects to the MQTT broker, subscribes to its command topic,
pretends to do the work, and reports status back on its status topic.

## Setup

```
cd examples/fake_robots
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

In one terminal:
```
python fake_rover.py
```

In another terminal, send a command:
```
curl -X POST http://localhost:8000/command \
  -H "Content-Type: application/json" \
  -d '{"text": "move the rover forward 3 meters"}'
```

The rover terminal should show the command being received and executed.

## Available robots

- `fake_rover.py` — wheeled rover, supports move/stop/rotate
- `fake_arm.py` — robotic arm (coming next)
- `fake_bot.py` — companion bot (coming after that)

## Topics

| Direction | Topic | Example |
|-----------|-------|---------|
| Master → Robot | `robots/<name>/command` | `robots/rover/command` |
| Robot → Master | `robots/<name>/status` | `robots/rover/status` | 