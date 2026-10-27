#pragma once
// Réglages modifiables depuis la page de configuration ("/") et enregistrés en mémoire (NVS).
// Les constantes de config.h servent de valeurs par défaut.

#include <Arduino.h>
#include <map>

struct Settings {
  uint32_t measureMs;       // intervalle entre deux mesures des sondes (ms)
  uint32_t pumpOnMs;        // durée de marche de la pompe (ms)
  uint32_t pumpOffMs;       // durée d'arrêt de la pompe (ms)
  bool pumpMoisture;        // mode automatique de la pompe : selon l'humidité (sinon cycle marche / arrêt)
  uint8_t pumpMoistureLow;  // arrosage démarré sous ce seuil (%)
  uint8_t pumpMoistureHigh; // arrosage arrêté à partir de ce seuil (%)
  uint16_t lightStartMin;   // heure d'allumage de l'éclairage (minutes depuis minuit)
  uint32_t lightOnMs;       // durée d'allumage de l'éclairage (ms), 24 h max
  uint16_t moistureDry;     // valeur brute sonde à l'air (0 %)
  uint16_t moistureWet;     // valeur brute sonde dans l'eau (100 %)

  void load();              // valeurs enregistrées, ou valeurs par défaut de config.h
  void save() const;
  void reset();             // efface les valeurs enregistrées et revient aux valeurs par défaut
  // Retourne un message d'erreur, vide si les valeurs sont acceptables
  String validate() const;
};

// Noms des sondes de température, indexés par l'identifiant de la sonde.
// Une sonde sans nom ne publie pas ses mesures sur MQTT.
class SensorNames {
public:
  String get(const String &id);                          // "" si aucun nom
  void set(const String &id, const String &name);        // name vide : efface le nom
  // Retourne un message d'erreur, vide si le nom est acceptable pour un topic MQTT
  static String validate(const String &name);
  void clear();

private:
  static String key(const String &id);
  std::map<String, String> _cache;
};

extern Settings settings;
extern SensorNames sensorNames;
