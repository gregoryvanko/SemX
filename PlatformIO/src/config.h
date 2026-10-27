#pragma once
// ── Setup ──────────────────────────────────────────────────────────────────────
constexpr int32_t CONFIG_BAUDRATE = 115200;
constexpr int32_t CONFIG_MESURE_INTERVAL = 10000;   // intervalle de mesure par défaut (ms), 2 s à 1 h
constexpr const char* CONFIG_DEVICE_NAME = "semix";  // nom d'appareil par défaut (modifiable sur /status), préfixe des topics MQTT
constexpr uint8_t CONFIG_DS18B20_PIN = 4;         // GPIO du bus 1-Wire des sondes DS18B20
constexpr uint8_t CONFIG_DS18B20_RESOLUTION = 12; // 9 à 12 bits
constexpr uint8_t CONFIG_MOISTURE_PIN = 34;       // GPIO de l'ADC1 (32 à 39) relié à AOUT de la sonde
constexpr uint8_t CONFIG_MOISTURE_SAMPLES = 16;   // lectures ADC moyennées par mesure
constexpr uint16_t CONFIG_MOISTURE_DRY = 2800;    // valeur brute sonde à l'air (0 %)
constexpr uint16_t CONFIG_MOISTURE_WET = 1200;    // valeur brute sonde dans l'eau (100 %)
constexpr uint8_t CONFIG_RELAY_Pump_PIN = 26;      // GPIO du relais de la pompe
constexpr uint32_t CONFIG_PUMP_ON_DURATION = 10000;   // durée de marche de la pompe (ms)
constexpr uint32_t CONFIG_PUMP_OFF_DURATION = 60000;  // durée d'arrêt de la pompe (ms)
constexpr bool CONFIG_PUMP_MOISTURE_ENABLED = false;  // mode par défaut : arrosage selon l'humidité (sinon cycle)
constexpr uint8_t CONFIG_PUMP_MOISTURE_LOW = 40;      // seuil de démarrage de l'arrosage (%)
constexpr uint8_t CONFIG_PUMP_MOISTURE_HIGH = 80;     // seuil d'arrêt de l'arrosage (%)

constexpr uint8_t CONFIG_RELAY_Light_PIN = 27;         // GPIO du relais d'éclairage
constexpr uint8_t CONFIG_LIGHT_START_HOUR = 6;         // heure d'allumage de l'éclairage (heure locale)
constexpr uint8_t CONFIG_LIGHT_START_MINUTE = 0;       // minute d'allumage de l'éclairage
constexpr uint32_t CONFIG_LIGHT_ON_DURATION = 16UL * 3600000UL;  // durée d'allumage de l'éclairage (ms) : 16 h, 24 h max
static_assert(CONFIG_LIGHT_ON_DURATION <= 24UL * 3600000UL, "CONFIG_LIGHT_ON_DURATION ne peut pas dépasser 24 h");

// ── Heure réseau ───────────────────────────────────────────────────────────────
constexpr const char* CONFIG_NTP_SERVER = "pool.ntp.org";
constexpr const char* CONFIG_TIMEZONE = "CET-1CEST,M3.5.0,M10.5.0/3"; // Europe/Bruxelles, heure d'été auto
