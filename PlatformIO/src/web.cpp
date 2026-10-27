#include "web.h"

#include <ArduinoJson.h>
#include <ESPConnect.h>
#include <time.h>

#include "config.h"
#include "devices.h"
#include "relays.h"
#include "sensors.h"
#include "settings.h"

// Serial log of the exchanges with the configuration page:
//   "[SemX] #<client> → <message>"     message received from the page
//   "[SemX] #<client> ← OK|ERREUR …"   answer sent to the page
//   "[SemX] #<client> : …"             action carried out
// The periodic state refresh (every 2 s) is not logged.
#define WEB_LOG(fmt, ...) Serial.printf("[SemX] " fmt "\n", ##__VA_ARGS__)

namespace {

const char *relayName(const String &relay) { return relay == "pump" ? "pompe" : "éclairage"; }

String duration(uint32_t ms) {
  uint32_t s = ms / 1000;
  String out;
  if (s >= 3600) out += String(s / 3600) + " h ";
  if (s % 3600 >= 60) out += String(s % 3600 / 60) + " min ";
  if (s % 60 || out.isEmpty()) out += String(s % 60) + " s ";
  out.trim();
  return out;
}

// Current state and settings, sent to the configuration page
String stateJson() {
  JsonDocument doc;
  doc["type"] = "state";
  doc["device"] = espConnect.deviceName();
  struct tm now;
  if (getLocalTime(&now, 0)) {
    char buf[9];
    strftime(buf, sizeof(buf), "%H:%M:%S", &now);
    doc["time"] = buf;
  }
  doc["pump"] = relais_Pump.isOn();
  doc["light"] = relais_Light.isOn();
  doc["pumpMode"] = modeName(pumpMode);
  doc["lightMode"] = modeName(lightMode);
  doc["soilDry"] = soilDry;

  JsonObject moisture = doc["moisture"].to<JsonObject>();
  moisture["raw"] = sol.raw();
  moisture["mv"] = sol.millivolts();
  moisture["valid"] = sol.valid();
  if (sol.valid()) moisture["percent"] = serialized(String(sol.percent(), 1));

  JsonArray list = doc["sensors"].to<JsonArray>();
  for (const SensorDS18B20::Sensor &sonde : sondes.sensors()) {
    JsonObject s = list.add<JsonObject>();
    s["id"] = sonde.id;
    s["name"] = sensorNames.get(sonde.id);
    s["valid"] = sonde.valid;
    if (sonde.valid) s["t"] = serialized(String(sonde.temperature, 2));
  }

  JsonObject cfg = doc["cfg"].to<JsonObject>();
  cfg["measure"] = settings.measureMs / 1000;
  cfg["pumpOn"] = settings.pumpOnMs / 1000;
  cfg["pumpOff"] = settings.pumpOffMs / 1000;
  cfg["moistLow"] = settings.pumpMoistureLow;
  cfg["moistHigh"] = settings.pumpMoistureHigh;
  cfg["lightStart"] = settings.lightStartMin;
  cfg["lightOn"] = settings.lightOnMs / 60000;
  cfg["dry"] = settings.moistureDry;
  cfg["wet"] = settings.moistureWet;

  String out;
  serializeJson(doc, out);
  return out;
}

void sendResult(uint32_t clientId, bool ok, const String &msg, bool reload = false) {
  JsonDocument doc;
  doc["type"] = "result";
  doc["ok"] = ok;
  doc["msg"] = msg;
  if (reload) doc["reload"] = true;
  String out;
  serializeJson(doc, out);
  espConnect.wsSend(clientId, out);
  WEB_LOG("#%lu ← %s %s", (unsigned long)clientId, ok ? "OK" : "ERREUR", msg.c_str());
}

}  // namespace

void broadcastState() {
  if (espConnect.wsClientCount() > 0) espConnect.wsSend(stateJson());
}

void handleConfigMessage(uint32_t clientId, const String &message) {
  WEB_LOG("#%lu → %s", (unsigned long)clientId, message.c_str());
  JsonDocument doc;
  if (DeserializationError error = deserializeJson(doc, message)) {
    WEB_LOG("#%lu : message ignoré (JSON invalide : %s)", (unsigned long)clientId, error.c_str());
    return;
  }
  String cmd = doc["cmd"] | "";

  if (cmd == "get") {
    espConnect.wsSend(clientId, stateJson());
    WEB_LOG("#%lu ← état complet envoyé", (unsigned long)clientId);

  } else if (cmd == "save") {
    Settings s = settings;
    s.measureMs = (doc["measure"] | 0UL) * 1000UL;
    s.pumpOnMs = (doc["pumpOn"] | 0UL) * 1000UL;
    s.pumpOffMs = (doc["pumpOff"] | 0UL) * 1000UL;
    s.pumpMoistureLow = doc["moistLow"] | 0U;
    s.pumpMoistureHigh = doc["moistHigh"] | 0U;
    s.lightStartMin = doc["lightStart"] | 0U;
    s.lightOnMs = (doc["lightOn"] | 0UL) * 60000UL;
    s.moistureDry = doc["dry"] | 0U;
    s.moistureWet = doc["wet"] | 0U;
    String error = s.validate();
    if (!error.isEmpty()) {
      sendResult(clientId, false, "Erreur : " + error);
      return;
    }
    settings = s;
    settings.save();
    WEB_LOG("#%lu : réglages enregistrés — mesure toutes les %s, pompe marche %s / arrêt %s, "
            "humidité %u %% → %u %%, éclairage %02u:%02u pendant %s, calibration sec %u / humide %u",
            (unsigned long)clientId, duration(settings.measureMs).c_str(), duration(settings.pumpOnMs).c_str(),
            duration(settings.pumpOffMs).c_str(), settings.pumpMoistureLow, settings.pumpMoistureHigh,
            settings.lightStartMin / 60, settings.lightStartMin % 60, duration(settings.lightOnMs).c_str(),
            settings.moistureDry, settings.moistureWet);
    sol.setCalibration(settings.moistureDry, settings.moistureWet);
    sol.measure();
    sendResult(clientId, true, "Enregistré.", true);
    broadcastState();

  } else if (cmd == "reset") {
    settings.reset();
    WEB_LOG("#%lu : retour aux valeurs par défaut de config.h", (unsigned long)clientId);
    if (pumpMode == RelayMode::Auto || pumpMode == RelayMode::Moisture)
      setRelayMode(relais_Pump, pumpMode, settings.pumpMoisture ? RelayMode::Moisture : RelayMode::Auto);
    sol.setCalibration(settings.moistureDry, settings.moistureWet);
    sol.measure();
    sendResult(clientId, true, "Valeurs par défaut rétablies.", true);
    broadcastState();

  } else if (cmd == "name") {
    String id = doc["id"] | "";
    String name = doc["name"] | "";
    name.trim();
    if (sondes.indexOf(id) < 0) {
      sendResult(clientId, false, "Sonde introuvable.");
      return;
    }
    String error = SensorNames::validate(name);
    for (const SensorDS18B20::Sensor &sonde : sondes.sensors()) {
      if (error.isEmpty() && !name.isEmpty() && sonde.id != id && sensorNames.get(sonde.id) == name)
        error = "nom déjà utilisé par une autre sonde";
    }
    if (!error.isEmpty()) {
      sendResult(clientId, false, "Erreur : " + error);
      return;
    }
    sensorNames.set(id, name);
    applySensorNames();
    if (name.isEmpty()) WEB_LOG("#%lu : sonde %s sans nom (non publiée)", (unsigned long)clientId, id.c_str());
    else WEB_LOG("#%lu : sonde %s nommée « %s »", (unsigned long)clientId, id.c_str(), name.c_str());
    sendResult(clientId, true, name.isEmpty() ? "Enregistré : la sonde n'est plus publiée." : "Enregistré.");
    broadcastState();

  } else if (cmd == "scan") {
    WEB_LOG("#%lu : recherche des sondes", (unsigned long)clientId);
    sondes.scan();
    applySensorNames();
    sendResult(clientId, true, String(sondes.count()) + " sonde(s) détectée(s).");
    broadcastState();

  } else if (cmd == "mode") {
    String relay = doc["relay"] | "";
    RelayMode mode;
    if ((relay != "pump" && relay != "light") || !parseMode(doc["mode"] | "", relay == "pump", mode)) {
      WEB_LOG("#%lu : commande de mode invalide ignorée", (unsigned long)clientId);
      return;
    }
    if (relay == "pump") setRelayMode(relais_Pump, pumpMode, mode);
    else setRelayMode(relais_Light, lightMode, mode);
    WEB_LOG("#%lu : %s en mode %s", (unsigned long)clientId, relayName(relay), modeName(mode));
    broadcastState();

  } else if (cmd == "moisture") {
    WEB_LOG("#%lu : lecture immédiate de la sonde d'humidité", (unsigned long)clientId);
    sol.measure();
    espConnect.wsSend(clientId, stateJson());
    WEB_LOG("#%lu ← état complet envoyé", (unsigned long)clientId);

  } else {
    WEB_LOG("#%lu : commande inconnue « %s » ignorée", (unsigned long)clientId, cmd.c_str());
  }
}

void webLoop() {
  static uint32_t stateLast = 0;
  if (millis() - stateLast >= 2000) {
    stateLast = millis();
    broadcastState();
  }
}
