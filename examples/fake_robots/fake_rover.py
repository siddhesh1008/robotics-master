"""
Fake rover. Subscribes to robots/rover/command, simulates driving,
reports status back.

Run:
    python fake_rover.py
"""

import time
from shared.base_robot import BaseRobot


class FakeRover(BaseRobot):
    def __init__(self):
        super().__init__(name="rover")

    def handle_command(self, command: dict) -> dict:
        action = command.get("action", "").lower()
        params = command.get("parameters", {})

        if action == "move":
            distance = params.get("distance", 0)
            direction = params.get("direction", "forward")
            print(f"  [rover] driving {direction} {distance} units...")
            time.sleep(2)  # pretend the wheels are turning
            return {"moved": distance, "direction": direction}

        elif action in ("stop", "halt"):
            print("  [rover] stopping")
            return {"stopped": True}

        elif action == "rotate":
            angle = params.get("angle", 0)
            print(f"  [rover] rotating {angle} degrees...")
            time.sleep(1)
            return {"rotated": angle}

        else:
            print(f"  [rover] unknown action: {action}")
            return {"unknown_action": action}


if __name__ == "__main__":
    FakeRover().run()