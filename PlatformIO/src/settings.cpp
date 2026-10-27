#include "settings.h"

#include <Preferences.h>

#include "config.h"

Settings settings;
SensorNames sensorNames;

namespace {

constexpr const char *NVS_SETTINGS = "semix";
constexpr const char *NVS_NAMES = "semix_ds";
constexpr uint32_t DAY_MS = 24UL * 3600000UL;

// Preferences journalise une erreur quand la clé n'existe pas encore : on vérifie sa présence avant de la lire.
uint32_t readUInt(Preferences &p, const char *key, uint32_t fallback) {
  return p.isKey(key) ? p.getUInt(key, fallback) : fallback;
}

}  // namespace

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

void Settings::load() {
  Preferences p;
  p.begin(NVS_SETTINGS, true);
  measureMs = readUInt(p, "measure", CONFIG_MESURE_INTERVAL);
  pumpOnMs = readUInt(p, "pumpOn", CONFIG_PUMP_ON_DURATION);
  pumpOffMs = readUInt(p, "pumpOff", CONFIG_PUMP_OFF_DURATION);
  pumpMoisture = readUInt(p, "pumpMoist", CONFIG_PUMP_MOISTURE_ENABLED);
  pumpMoistureLow = readUInt(p, "pumpMoistLow", CONFIG_PUMP_MOISTURE_LOW);
  pumpMoistureHigh = readUInt(p, "pumpMoistHigh", CONFIG_PUMP_MOISTURE_HIGH);
  lightStartMin = readUInt(p, "lightStart", CONFIG_LIGHT_START_HOUR * 60 + CONFIG_LIGHT_START_MINUTE);
  lightOnMs = readUInt(p, "lightOn", CONFIG_LIGHT_ON_DURATION);
  moistureDry = readUInt(p, "moistDry", CONFIG_MOISTURE_DRY);
  moistureWet = readUInt(p, "moistWet", CONFIG_MOISTURE_WET);
  p.end();

  // Valeurs enregistrées incohérentes : retour aux valeurs par défaut
  String error = validate();
  if (!error.isEmpty()) {
    Serial.printf("[Settings] Réglages enregistrés invalides (%s), valeurs par défaut utilisées\n", error.c_str());
    reset();
  }
}

void Settings::save() const {
  Preferences p;
  p.begin(NVS_SETTINGS, false);
  p.putUInt("measure", measureMs);
  p.putUInt("pumpOn", pumpOnMs);
  p.putUInt("pumpOff", pumpOffMs);
  p.putUInt("pumpMoist", pumpMoisture);
  p.putUInt("pumpMoistLow", pumpMoistureLow);
  p.putUInt("pumpMoistHigh", pumpMoistureHigh);
  p.putUInt("lightStart", lightStartMin);
  p.putUInt("lightOn", lightOnMs);
  p.putUInt("moistDry", moistureDry);
  p.putUInt("moistWet", moistureWet);
  p.end();
  Serial.println("[Settings] Réglages enregistrés");
}

void Settings::reset() {
  Preferences p;
  p.begin(NVS_SETTINGS, false);
  p.clear();
  p.end();
  measureMs = CONFIG_MESURE_INTERVAL;
  pumpOnMs = CONFIG_PUMP_ON_DURATION;
  pumpOffMs = CONFIG_PUMP_OFF_DURATION;
  pumpMoisture = CONFIG_PUMP_MOISTURE_ENABLED;
  pumpMoistureLow = CONFIG_PUMP_MOISTURE_LOW;
  pumpMoistureHigh = CONFIG_PUMP_MOISTURE_HIGH;
  lightStartMin = CONFIG_LIGHT_START_HOUR * 60 + CONFIG_LIGHT_START_MINUTE;
  lightOnMs = CONFIG_LIGHT_ON_DURATION;
  moistureDry = CONFIG_MOISTURE_DRY;
  moistureWet = CONFIG_MOISTURE_WET;
}

String Settings::validate() const {
  if (measureMs < 2000 || measureMs > 3600000UL) return "intervalle de mesure : 2 s à 1 h";
  if (pumpOnMs < 1000 || pumpOnMs > DAY_MS) return "durée de marche de la pompe : 1 s à 24 h";
  if (pumpOffMs < 1000 || pumpOffMs > DAY_MS) return "durée d'arrêt de la pompe : 1 s à 24 h";
  if (pumpMoistureHigh > 100) return "seuil d'arrêt de l'arrosage : 100 % maximum";
  if (pumpMoistureLow >= pumpMoistureHigh) return "le seuil de démarrage doit être inférieur au seuil d'arrêt";
  if (lightStartMin >= 24 * 60) return "heure d'allumage invalide";
  if (lightOnMs > DAY_MS) return "durée d'allumage de l'éclairage : 24 h maximum";
  if (moistureDry > 4095 || moistureWet > 4095) return "valeurs de calibration : 0 à 4095";
  if (moistureDry == moistureWet) return "les valeurs « sec » et « humide » doivent être différentes";
  return String();
}

// ---------------------------------------------------------------------------
// SensorNames
// ---------------------------------------------------------------------------

// Les clés NVS sont limitées à 15 caractères : on garde la famille et le numéro de série
// de la sonde (14 premiers caractères de l'identifiant, sans l'octet de CRC).
String SensorNames::key(const String &id) { return "n" + id.substring(0, 14); }

String SensorNames::get(const String &id) {
  auto it = _cache.find(id);
  if (it != _cache.end()) return it->second;

  Preferences p;
  p.begin(NVS_NAMES, true);
  String k = key(id);
  String name = p.isKey(k.c_str()) ? p.getString(k.c_str(), "") : String();
  p.end();
  _cache[id] = name;
  return name;
}

void SensorNames::set(const String &id, const String &name) {
  Preferences p;
  p.begin(NVS_NAMES, false);
  String k = key(id);
  if (name.isEmpty()) {
    if (p.isKey(k.c_str())) p.remove(k.c_str());
  } else {
    p.putString(k.c_str(), name);
  }
  p.end();
  _cache[id] = name;
}

String SensorNames::validate(const String &name) {
  if (name.length() > 32) return "32 caractères maximum";
  for (char c : name)
    if (!isalnum((unsigned char)c) && c != '_' && c != '-') return "lettres, chiffres, « _ » et « - » uniquement";
  return String();
}

void SensorNames::clear() {
  Preferences p;
  p.begin(NVS_NAMES, false);
  p.clear();
  p.end();
  _cache.clear();
}
