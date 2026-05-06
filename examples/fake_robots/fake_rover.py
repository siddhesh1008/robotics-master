"""
Fake rover with position tracking. Subscribes to robots/rover/command,
simulates driving and rotating, reports position in status messages.

Run:
    python fake_rover.py

State:
    x, y     position in meters (0,0 is origin)
    heading  angle in degrees (0 = east, 90 = north, 180 = west, 270 = south)
"""

import math
import time
from shared.base_robot import BaseRobot


class FakeRover(BaseRobot):
    def __init__(self):
        super().__init__(name="rover")
        self.x = 0.0
        self.y = 0.0
        self.heading = 90.0  # facing north by default

    def position(self) -> dict:
        return {
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "heading": round(self.heading, 1),
        }

    def publish_status(self, state: str, payload: dict):
        payload = {**payload, "position": self.position()}
        super().publish_status(state, payload)

    def _get_angle(self, params: dict) -> float:
        # Accept any of these keys for rotation amount
        for key in ("angle", "degrees", "deg", "rotation", "amount"):
            if key in params:
                return float(params[key])
        return 0.0

    def _get_distance(self, params: dict) -> float:
        for key in ("distance", "meters", "amount"):
            if key in params:
                return float(params[key])
        return 0.0

    def handle_command(self, command: dict) -> dict:
        action = command.get("action", "").lower()
        params = command.get("parameters", {})

        if action == "move":
            distance = self._get_distance(params)
            direction = params.get("direction", "forward").lower()

            if direction in ("backward", "back", "reverse"):
                distance = -distance

            radians = math.radians(self.heading)
            self.x += distance * math.cos(radians)
            self.y += distance * math.sin(radians)

            print(f"  [rover] driving {direction} {abs(distance)}m -> ({self.x:.2f}, {self.y:.2f})")
            time.sleep(2)
            return {"moved": distance, "direction": direction, "position": self.position()}

        elif action in ("stop", "halt"):
            print("  [rover] stopping")
            return {"stopped": True, "position": self.position()}

        elif action == "rotate":
            angle = self._get_angle(params)
            direction = params.get("direction", "clockwise").lower()

            if direction in ("clockwise", "right", "cw"):
                self.heading -= angle
            else:
                self.heading += angle

            self.heading = self.heading % 360

            print(f"  [rover] rotating {angle}° {direction} -> heading {self.heading:.1f}°")
            time.sleep(1)
            return {"rotated": angle, "direction": direction, "heading": self.heading}

        elif action in ("reset", "home"):
            self.x, self.y, self.heading = 0.0, 0.0, 90.0
            print("  [rover] reset to origin")
            return {"reset": True, "position": self.position()}

        else:
            print(f"  [rover] unknown action: {action}")
            return {"unknown_action": action, "position": self.position()}


if __name__ == "__main__":
    FakeRover().run()