"""
Base class for all fake (and eventually real) CRCS robots.

A robot in CRCS:
  - Subscribes to robots/<name>/command   (receives orders)
  - Publishes to   robots/<name>/status   (reports back)

Subclasses just override handle_command() with their own logic.
"""

import json
import time
import os
import paho.mqtt.client as mqtt


class BaseRobot:
    def __init__(self, name: str, mqtt_host: str = None, mqtt_port: int = None):
        self.name = name
        self.mqtt_host = mqtt_host or os.getenv("MQTT_HOST", "localhost")
        self.mqtt_port = mqtt_port or int(os.getenv("MQTT_PORT", "1883"))

        self.command_topic = f"robots/{name}/command"
        self.status_topic = f"robots/{name}/status"

        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"robot-{name}",
        )
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"[{self.name}] connected to MQTT (rc={rc})")
        client.subscribe(self.command_topic, qos=1)
        print(f"[{self.name}] subscribed to {self.command_topic}")
        self.publish_status("online", {"message": f"{self.name} ready"})

    def _on_message(self, client, userdata, msg):
        try:
            command = json.loads(msg.payload.decode())
        except json.JSONDecodeError:
            print(f"[{self.name}] received invalid JSON")
            self.publish_status("error", {"reason": "invalid JSON"})
            return

        print(f"[{self.name}] received command: {command}")
        self.publish_status("busy", {"command": command})

        try:
            result = self.handle_command(command)
            self.publish_status("done", {"command": command, "result": result})
        except Exception as e:
            print(f"[{self.name}] error handling command: {e}")
            self.publish_status("error", {"command": command, "reason": str(e)})

    def publish_status(self, state: str, payload: dict):
        msg = {
            "robot": self.name,
            "state": state,
            "timestamp": time.time(),
            **payload,
        }
        self.client.publish(self.status_topic, json.dumps(msg), qos=1)
        print(f"[{self.name}] status -> {state}")

    def handle_command(self, command: dict) -> dict:
        """Override this in subclasses."""
        raise NotImplementedError("Subclasses must implement handle_command")

    def run(self):
        print(f"[{self.name}] connecting to {self.mqtt_host}:{self.mqtt_port}")
        self.client.connect(self.mqtt_host, self.mqtt_port, 60)
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            print(f"\n[{self.name}] shutting down")
            self.publish_status("offline", {"message": f"{self.name} stopped"})
            self.client.disconnect()