#include "relays.h"

#include <ESPConnect.h>
#include <Preferences.h>
#include <esp_system.h>
#include <time.h>

#include "config.h"
#include "devices.h"
#include "settings.h"
#include "web.h"

RelayMode pumpMode = RelayMode::Auto;
RelayMode lightMode = RelayMode::Auto;
bool soilDry = false;

namespace {

uint32_t pumpLast = 0;  // millis() of the last pump cycle change

// On the first valid reading (after a restart or when the Moisture mode is selected), the soil
// is considered dry as long as it is below the high threshold.
bool soilDryInit = false;

// Pump in Auto mode: on for settings.pumpOnMs, then off for settings.pumpOffMs (non-blocking)
// Pump in Moisture mode: on while the soil is dry (below the low threshold, until the high one)
void pumpLoop() {
  if (pumpMode == RelayMode::Auto) {
    uint32_t pumpDuration = relais_Pump.isOn() ? settings.pumpOnMs : settings.pumpOffMs;
    if (millis() - pumpLast >= pumpDuration) {
      pumpLast = millis();
      relais_Pump.toggle();
      broadcastState();
    }
  }

  if (pumpMode == RelayMode::Moisture && soilDry != relais_Pump.isOn()) {
    soilDry ? relais_Pump.turnOn() : relais_Pump.turnOff();
    broadcastState();
  }
}

// The lamps are switched by a pulse on their on / off button: their state cannot be read on the
// relay, it is remembered in NVS (separate namespace, kept by Settings::reset()) at every change.
constexpr const char *NVS_LIGHT = "semix_light";

bool loadLightState() {
  Preferences p;
  p.begin(NVS_LIGHT, false);
  bool on = p.isKey("on") && p.getBool("on", false);
  p.end();
  return on;
}

void saveLightState(bool on) {
  Preferences p;
  p.begin(NVS_LIGHT, false);
  p.putBool("on", on);
  p.end();
}

// Light schedule (automatic mode) on network time: on every day at settings.lightStartMin
// for settings.lightOnMs, off the rest of the day.
// The light keeps its state at startup until the time is synchronised.
void lightLoop() {
  static uint32_t lightLast = 0;
  if (lightMode != RelayMode::Auto || millis() - lightLast < 1000) return;
  lightLast = millis();
  struct tm now;
  if (!getLocalTime(&now, 0)) return;
  const int32_t start = settings.lightStartMin * 60;
  const int32_t secondsOfDay = now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec;
  const uint32_t elapsed = (secondsOfDay - start + 86400) % 86400;
  const bool lightOn = elapsed < settings.lightOnMs / 1000;
  if (lightOn != relais_Light.target()) {
    lightOn ? relais_Light.turnOn() : relais_Light.turnOff();
    broadcastState();
  }
}

const char *const RELAY_TOPICS[] = {"/pump/state", "/pump/mode", "/light/state", "/light/mode"};

// Subscribe to "<device>/cmd/#", and follow the device name when it is changed on /status
void subscribeCommands() {
  static String subscribed;
  String name = espConnect.deviceName();
  if (name == subscribed) return;
  if (!subscribed.isEmpty()) espConnect.unsubscribe(subscribed + "/cmd/#");
  espConnect.subscribe(name + "/cmd/#");
  subscribed = name;
}

// Publish the relay states and modes (retained) on "<device>/pump/state", "<device>/pump/mode",
// "<device>/light/state" and "<device>/light/mode" when they change or when MQTT (re)connects.
// After a device rename on /status, the retained messages of the former name are cleared.
void publishRelays() {
  static bool wasConnected = false;
  static String published;  // device name of the last publication
  static bool pumpOn, lightOn;
  static RelayMode pumpM, lightM;
  bool connected = espConnect.isMqttConnected();
  bool reconnected = connected && !wasConnected;
  wasConnected = connected;
  if (!connected) return;

  String base = espConnect.deviceName();
  if (base != published) {
    if (!published.isEmpty())
      for (const char *topic : RELAY_TOPICS) espConnect.publish(published + topic, "", true);
    published = base;
    reconnected = true;
  }
  if (reconnected || pumpOn != relais_Pump.isOn()) {
    pumpOn = relais_Pump.isOn();
    espConnect.publish(base + "/pump/state", relais_Pump.getStateString(), true);
  }
  if (reconnected || pumpM != pumpMode) {
    pumpM = pumpMode;
    espConnect.publish(base + "/pump/mode", modeName(pumpMode), true);
  }
  if (reconnected || lightOn != relais_Light.isOn()) {
    lightOn = relais_Light.isOn();
    espConnect.publish(base + "/light/state", relais_Light.getStateString(), true);
  }
  if (reconnected || lightM != lightMode) {
    lightM = lightMode;
    espConnect.publish(base + "/light/mode", modeName(lightMode), true);
  }
}

}  // namespace

void updateSoilDry() {
  if (!sol.valid()) {
    soilDry = false;  // no reliable reading: no watering
  } else if (!soilDryInit) {
    soilDry = sol.percent() < settings.pumpMoistureHigh;
    soilDryInit = true;
  } else if (sol.percent() < settings.pumpMoistureLow) {
    soilDry = true;
  } else if (sol.percent() >= settings.pumpMoistureHigh) {
    soilDry = false;
  }
}

const char *modeName(RelayMode mode) {
  switch (mode) {
    case RelayMode::Moisture: return "moisture";
    case RelayMode::On: return "on";
    case RelayMode::Off: return "off";
    default: return "auto";
  }
}

bool parseMode(String value, bool isPump, RelayMode &mode) {
  value.trim();
  value.toLowerCase();
  if (value == "auto") mode = RelayMode::Auto;
  else if (value == "moisture" && isPump) mode = RelayMode::Moisture;
  else if (value == "on") mode = RelayMode::On;
  else if (value == "off") mode = RelayMode::Off;
  else return false;
  return true;
}

// In Auto, the pump cycle restarts with the off period. In Moisture, the pump follows the soil
// moisture as soon as it is measured (immediately). The pump automatic mode (Auto or Moisture) is saved.
void setPumpMode(RelayMode mode) {
  pumpMode = mode;
  if (mode == RelayMode::On) {
    if (!relais_Pump.isOn()) relais_Pump.turnOn();
  } else if (relais_Pump.isOn()) {
    relais_Pump.turnOff();
  }
  pumpLast = millis();
  if (mode == RelayMode::Auto || mode == RelayMode::Moisture) {
    bool moisture = mode == RelayMode::Moisture;
    if (settings.pumpMoisture != moisture) {
      settings.pumpMoisture = moisture;
      settings.save();
    }
  }
  if (mode == RelayMode::Moisture) {
    soilDryInit = false;
    sol.measure();
  }
}

// In Auto, the light follows its schedule again within one second.
void setLightMode(RelayMode mode) {
  if (mode == RelayMode::Moisture) return;
  lightMode = mode;
  if (mode == RelayMode::On) relais_Light.turnOn();
  else if (mode == RelayMode::Off) relais_Light.turnOff();
}

bool setLightActual(bool on) { return relais_Light.setActual(on); }

void relaysBegin() {
  // Start pump relay (off at startup) in its saved automatic mode
  relais_Pump.begin();
  pumpMode = settings.pumpMoisture ? RelayMode::Moisture : RelayMode::Auto;

  // Start light relay (open) with the lamp state remembered before the restart. After a power cut
  // the lamps are considered off (CONFIG_LIGHT_OFF_AFTER_POWER_ON).
  const esp_reset_reason_t reason = esp_reset_reason();
  const bool powerOn = reason == ESP_RST_POWERON || reason == ESP_RST_BROWNOUT;
  const bool lightOn = (CONFIG_LIGHT_OFF_AFTER_POWER_ON && powerOn) ? false : loadLightState();
  Serial.printf("[Éclairage] Redémarrage (%s) : état enregistré %s\n",
                powerOn ? "mise sous tension" : "logiciel", lightOn ? "repris (allumées)" : "ignoré ou éteintes");
  relais_Light.onChange([](bool on) {
    saveLightState(on);
    broadcastState();
  });
  relais_Light.begin(lightOn);
  saveLightState(lightOn);
}

void relaysLoop() {
  subscribeCommands();
  pumpLoop();
  lightLoop();
  // Pulses on the lamp button (non-blocking)
  relais_Light.loop();
  // Publish the relay states and modes on MQTT when they change
  publishRelays();
}

void handleMqttMessage(const String &topic, const String &payload) {
  Serial.printf("Message MQTT %s : %s\n", topic.c_str(), payload.c_str());
  String prefix = espConnect.deviceName() + "/cmd/";
  if (!topic.startsWith(prefix)) return;
  String cmd = topic.substring(prefix.length());
  if (cmd == "light/actual") {
    String value = payload;
    value.trim();
    value.toLowerCase();
    if (value != "on" && value != "off") {
      Serial.printf("Commande MQTT ignorée : « %s » (attendu : on ou off)\n", payload.c_str());
      return;
    }
    if (setLightActual(value == "on")) broadcastState();
    return;
  }
  RelayMode mode;
  if (cmd != "pump" && cmd != "light") return;
  if (!parseMode(payload, cmd == "pump", mode)) {
    Serial.printf("Commande MQTT ignorée : « %s » (attendu : auto, %son ou off)\n", payload.c_str(),
                  cmd == "pump" ? "moisture, " : "");
    return;
  }
  if (cmd == "pump") setPumpMode(mode);
  else setLightMode(mode);
  broadcastState();
}
