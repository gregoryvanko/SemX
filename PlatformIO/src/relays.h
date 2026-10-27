#pragma once
// Pilotage des relais de la pompe et de l'éclairage, et commandes / état sur MQTT.

#include <Arduino.h>
#include <RelayController.h>

// Relay mode set from the configuration page or MQTT:
//   Auto     : on / off cycle (pump) or daily schedule (light)
//   Moisture : pump only, watering on soil moisture (see updateSoilDry())
//   On / Off : forced on / off
// Forced modes are not saved: after a restart the pump is back in its saved automatic mode
// (Auto or Moisture, settings.pumpMoisture) and the light in Auto.
enum class RelayMode : uint8_t { Auto, Moisture, On, Off };
extern RelayMode pumpMode;
extern RelayMode lightMode;

// Watering on soil moisture: true from the moment the soil is below settings.pumpMoistureLow
// until it reaches settings.pumpMoistureHigh.
extern bool soilDry;

// Update soilDry from the last moisture measurement
void updateSoilDry();

const char *modeName(RelayMode mode);

// "auto", "moisture" (pump only), "on" or "off" (case-insensitive). Returns false for any other value.
bool parseMode(String value, bool isPump, RelayMode &mode);

// Force a relay on / off, or give it back to an automatic mode.
void setRelayMode(RelayController &relay, RelayMode &current, RelayMode mode);

// Start both relays (off) and the pump in its saved automatic mode
void relaysBegin();

// Pump cycle / watering, light schedule and MQTT state (to call from loop())
void relaysLoop();

// MQTT commands ("<device>" is the device name set on /status): "<device>/cmd/pump" ("auto", "moisture", "on" or "off")
// and "<device>/cmd/light" ("auto", "on" or "off") set the relay mode.
void handleMqttMessage(const String &topic, const String &payload);
