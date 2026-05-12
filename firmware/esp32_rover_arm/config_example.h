// ============================================================
//  CRCS Rover - configuration template
//  Copy this file to config.h and fill in your details.
//  config.h is gitignored, so your secrets stay local.
// ============================================================

#pragma once

// Your home WiFi (2.4 GHz only, ESP32 doesn't support 5 GHz)
const char* WIFI_SSID     = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// CRCS master MQTT broker
const char* MQTT_HOST     = "192.168.0.45";
const int   MQTT_PORT     = 1883;

// Unique client ID. Change if you have more than one rover on the network.
const char* CLIENT_ID     = "rover-esp32";