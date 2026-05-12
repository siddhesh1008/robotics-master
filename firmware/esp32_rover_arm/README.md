# CRCS Rover Firmware (ESP32)

C++ firmware for a real CRCS rover. Subscribes to `robots/rover/command` over MQTT, drives two DC motors through an L298N driver, and reports state back on `robots/rover/status`.

This is the real-hardware equivalent of `examples/fake_robots/fake_rover.py`.

## Hardware

- ESP32 WROOM-32 dev board (or any ESP32 with WiFi)
- L298N dual H-bridge motor driver
- 2× DC motors (tested with 12V 150 RPM geared motors)
- 12V power supply (bench supply or 3S battery)
- A 3D printed or otherwise built chassis with two driven wheels

## Wiring

| ESP32 GPIO | L298N pin | Function |
|------------|-----------|----------|
| 26         | IN1       | Motor A direction |
| 27         | IN2       | Motor A direction |
| 14         | ENA       | Motor A PWM speed |
| 25         | IN3       | Motor B direction |
| 33         | IN4       | Motor B direction |
| 32         | ENB       | Motor B PWM speed |
| GND        | GND       | Common ground (mandatory) |

Power:
- 12V supply to L298N `+12V` and `GND`
- ESP32 powered separately via USB
- All grounds tied together

**Pull the ENA and ENB jumpers off the L298N.** With jumpers on, motors run at fixed full speed and PWM is ignored.

## Flashing

1. Install [Arduino IDE 2.x](https://www.arduino.cc/en/software).
2. Add ESP32 board support: Preferences → Additional Boards Manager URLs → add `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`. Then Boards Manager → install **esp32 by Espressif Systems**.
3. Install required libraries (Library Manager):
   - **PubSubClient** by Nick O'Leary
   - **ArduinoJson** by Benoit Blanchon (v7.x)
4. Copy `config_example.h` to `config.h` in this folder.
5. Edit `config.h` with your WiFi SSID, password, and the IP of your CRCS master.
6. Select board: **ESP32 Dev Module**. Select the correct COM/USB port.
7. Open `esp32_rover_arm.ino`, upload. Hold the BOOT button if upload doesn't start ("Connecting...").

## First boot

Open Serial Monitor at **115200 baud**. You should see:

```
=== CRCS Rover Firmware ===
[WiFi] connecting...
[WiFi] connected, IP: 192.168.0.x
[MQTT] connecting ... ok
[MQTT] subscribed to robots/rover/command
[status] {"robot":"rover","state":"online",...}
```

On the CRCS master, the orchestrator log will show:
```
[orchestrator] rover -> online @ {'x': 0.0, 'y': 0.0, 'heading': 90.0}
```

## Calibration

Without wheel encoders, the rover uses dead reckoning. Two constants control accuracy:

```cpp
const float MS_PER_METER  = 2000.0;
const float MS_PER_DEGREE = 15.0;
```

To calibrate distance: place the rover on the floor, send `move forward 1 meter`, measure the actual distance traveled. Adjust `MS_PER_METER` proportionally and re-flash.

To calibrate rotation: send `rotate 360 degrees clockwise`, measure how far it actually rotated. Adjust `MS_PER_DEGREE` proportionally.

Expect drift to accumulate over time. Real odometry will require wheel encoders.

## Adjustments

If a motor spins the wrong way, flip the corresponding invert flag at the top of the sketch:
```cpp
const bool MOTOR_A_INVERT = true;
const bool MOTOR_B_INVERT = true;
```

If motors are too fast or too slow, change `DEFAULT_PWM` (0..255).

## Troubleshooting

| Symptom | Likely cause |
|---------|--------------|
| ESP32 connects to WiFi but not MQTT | Wrong `MQTT_HOST` IP, or firewall blocking port 1883 |
| Connects but motors don't move | ENA/ENB jumpers still on, or 12V supply not on |
| Motors run full speed regardless of PWM | ENA/ENB jumpers still on |
| ESP32 resets when motors start | Brownout. Don't power ESP32 from L298N's 5V rail |
| One motor wrong direction | Flip its `MOTOR_X_INVERT` flag |
| Position drifts a lot | Expected without encoders. Calibrate more carefully or add encoders |

## Topics

| Direction | Topic | Payload |
|-----------|-------|---------|
| Master → Rover | `robots/rover/command` | `{"action":"move","parameters":{"distance":1}}` |
| Rover → Master | `robots/rover/status` | `{"robot":"rover","state":"done","position":{...}}` |

Supported actions: `move`, `rotate`, `stop`, `reset`.