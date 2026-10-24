#pragma once
// ── Setup ──────────────────────────────────────────────────────────────────────
constexpr int32_t CONFIG_BAUDRATE = 115200;
constexpr int32_t CONFIG_MESURE_INTERVAL = 10000;
constexpr const char* CONFIG_DEVICE_NAME = "semix";
constexpr uint8_t CONFIG_DS18B20_PIN = 4;         // GPIO du bus 1-Wire des sondes DS18B20
constexpr uint8_t CONFIG_DS18B20_RESOLUTION = 12; // 9 à 12 bits
constexpr uint8_t CONFIG_MOISTURE_PIN = 34;       // GPIO de l'ADC1 (32 à 39) relié à AOUT de la sonde
constexpr uint8_t CONFIG_MOISTURE_SAMPLES = 16;   // lectures ADC moyennées par mesure
constexpr uint16_t CONFIG_MOISTURE_DRY = 2800;    // valeur brute sonde à l'air (0 %)
constexpr uint16_t CONFIG_MOISTURE_WET = 1200;    // valeur brute sonde dans l'eau (100 %)
