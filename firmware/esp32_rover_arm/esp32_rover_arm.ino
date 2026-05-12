// ============================================================
//  CRCS Rover Firmware - ESP32 + L298N + 2 DC motors
//  Differential drive, no encoders (dead reckoning)
//
//  Before flashing:
//    1. Copy config_example.h -> config.h
//    2. Fill in your WiFi and MQTT details in config.h
//    3. Install libraries: PubSubClient, ArduinoJson
// ============================================================

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <math.h>
#include "config.h"

// Motor pins
const int IN1 = 26;   // Motor A
const int IN2 = 27;
const int ENA = 14;
const int IN3 = 25;   // Motor B
const int IN4 = 33;
const int ENB = 32;

// PWM
const int PWM_FREQ = 1000;
const int PWM_RES  = 8;

// Direction inversion. Adjust per build.
const bool MOTOR_A_INVERT = true;
const bool MOTOR_B_INVERT = true;

// Default driving speed (0..255). Tune later.
const int DEFAULT_PWM = 150;

// Calibration (rough first guess, tune later).
const float MS_PER_METER  = 2000.0;
const float MS_PER_DEGREE = 15.0;

// MQTT topics
const char* TOPIC_COMMAND = "robots/rover/command";
const char* TOPIC_STATUS  = "robots/rover/status";

// Rover state
float pos_x   = 0.0;
float pos_y   = 0.0;
float heading = 90.0;   // degrees, 0=east, 90=north

WiFiClient espClient;
PubSubClient mqtt(espClient);

unsigned long lastHeartbeat = 0;

// ---------- Motor control ----------
void motorA(int speed, bool forward) {
  bool dir = MOTOR_A_INVERT ? !forward : forward;
  digitalWrite(IN1, dir ? HIGH : LOW);
  digitalWrite(IN2, dir ? LOW  : HIGH);
  ledcWrite(ENA, speed);
}

void motorB(int speed, bool forward) {
  bool dir = MOTOR_B_INVERT ? !forward : forward;
  digitalWrite(IN3, dir ? HIGH : LOW);
  digitalWrite(IN4, dir ? LOW  : HIGH);
  ledcWrite(ENB, speed);
}

void stopAll() {
  ledcWrite(ENA, 0);
  ledcWrite(ENB, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

// ---------- Drive primitives ----------
void driveForward(int pwm, unsigned long durationMs) {
  motorA(pwm, true);
  motorB(pwm, true);
  delay(durationMs);
  stopAll();
}

void driveBackward(int pwm, unsigned long durationMs) {
  motorA(pwm, false);
  motorB(pwm, false);
  delay(durationMs);
  stopAll();
}

void rotateClockwise(int pwm, unsigned long durationMs) {
  motorA(pwm, true);
  motorB(pwm, false);
  delay(durationMs);
  stopAll();
}

void rotateCounterClockwise(int pwm, unsigned long durationMs) {
  motorA(pwm, false);
  motorB(pwm, true);
  delay(durationMs);
  stopAll();
}

// ---------- Status publishing ----------
void publishStatus(const char* state, JsonDocument* extra = nullptr) {
  JsonDocument doc;
  doc["robot"] = "rover";
  doc["state"] = state;
  doc["timestamp"] = millis() / 1000.0;

  JsonObject pos = doc["position"].to<JsonObject>();
  pos["x"] = pos_x;
  pos["y"] = pos_y;
  pos["heading"] = heading;

  if (extra != nullptr) {
    for (JsonPair kv : extra->as<JsonObject>()) {
      doc[kv.key()] = kv.value();
    }
  }

  char buf[512];
  size_t n = serializeJson(doc, buf, sizeof(buf));
  mqtt.publish(TOPIC_STATUS, buf, n);

  Serial.print("[status] ");
  Serial.println(buf);
}

// ---------- Command handler ----------
void handleCommand(const JsonDocument& cmd) {
  const char* action = cmd["action"] | "";
  JsonObjectConst params = cmd["parameters"];

  {
    JsonDocument extra;
    extra["command"] = cmd;
    publishStatus("busy", &extra);
  }

  if (strcmp(action, "move") == 0) {
    float distance = params["distance"] | 0.0f;
    const char* direction = params["direction"] | "forward";
    bool forward = !(strcmp(direction, "backward") == 0
                  || strcmp(direction, "back") == 0
                  || strcmp(direction, "reverse") == 0);

    unsigned long ms = (unsigned long)(fabs(distance) * MS_PER_METER);
    Serial.printf("[cmd] move %s %.2fm for %lums\n", direction, distance, ms);

    if (forward) driveForward(DEFAULT_PWM, ms);
    else         driveBackward(DEFAULT_PWM, ms);

    float effective = forward ? distance : -distance;
    float rad = heading * M_PI / 180.0;
    pos_x += effective * cos(rad);
    pos_y += effective * sin(rad);
  }
  else if (strcmp(action, "rotate") == 0) {
    float angle = 0.0;
    if (params["angle"].is<float>())          angle = params["angle"];
    else if (params["degrees"].is<float>())   angle = params["degrees"];
    const char* direction = params["direction"] | "clockwise";
    bool cw = (strcmp(direction, "clockwise") == 0
            || strcmp(direction, "right") == 0
            || strcmp(direction, "cw") == 0);

    unsigned long ms = (unsigned long)(fabs(angle) * MS_PER_DEGREE);
    Serial.printf("[cmd] rotate %.1f deg %s for %lums\n", angle, direction, ms);

    if (cw) rotateClockwise(DEFAULT_PWM, ms);
    else    rotateCounterClockwise(DEFAULT_PWM, ms);

    if (cw) heading -= angle;
    else    heading += angle;
    while (heading <   0.0) heading += 360.0;
    while (heading >= 360.0) heading -= 360.0;
  }
  else if (strcmp(action, "stop") == 0 || strcmp(action, "halt") == 0) {
    stopAll();
    Serial.println("[cmd] stop");
  }
  else if (strcmp(action, "reset") == 0 || strcmp(action, "home") == 0) {
    stopAll();
    pos_x = 0.0;
    pos_y = 0.0;
    heading = 90.0;
    Serial.println("[cmd] reset to origin");
  }
  else {
    Serial.print("[cmd] unknown action: ");
    Serial.println(action);
  }

  publishStatus("done");
}

// ---------- MQTT callback ----------
void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  Serial.print("[MQTT] received on ");
  Serial.println(topic);

  JsonDocument cmd;
  DeserializationError err = deserializeJson(cmd, payload, length);
  if (err) {
    Serial.print("[MQTT] JSON parse error: ");
    Serial.println(err.c_str());
    return;
  }
  handleCommand(cmd);
}

// ---------- Connection ----------
void connectWiFi() {
  Serial.print("[WiFi] connecting");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("[WiFi] connected, IP: ");
  Serial.println(WiFi.localIP());
}

void connectMqtt() {
  while (!mqtt.connected()) {
    Serial.print("[MQTT] connecting ... ");
    if (mqtt.connect(CLIENT_ID)) {
      Serial.println("ok");
      mqtt.subscribe(TOPIC_COMMAND);
      Serial.printf("[MQTT] subscribed to %s\n", TOPIC_COMMAND);
      publishStatus("online");
    } else {
      Serial.print("failed rc=");
      Serial.print(mqtt.state());
      Serial.println(", retry in 3s");
      delay(3000);
    }
  }
}

// ---------- Setup / Loop ----------
void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println();
  Serial.println("=== CRCS Rover Firmware ===");

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  ledcAttach(ENA, PWM_FREQ, PWM_RES);
  ledcAttach(ENB, PWM_FREQ, PWM_RES);
  stopAll();

  connectWiFi();

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMqttMessage);
  mqtt.setBufferSize(512);
  connectMqtt();
}

void loop() {
  if (!mqtt.connected()) {
    connectMqtt();
  }
  mqtt.loop();

  if (millis() - lastHeartbeat > 10000) {
    lastHeartbeat = millis();
    JsonDocument extra;
    extra["message"] = "heartbeat";
    publishStatus("online", &extra);
  }
}