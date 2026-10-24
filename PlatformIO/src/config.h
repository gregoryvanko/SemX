#pragma once
// ── Setup ──────────────────────────────────────────────────────────────────────
constexpr int32_t CONFIG_BAUDRATE = 115200;
constexpr int32_t CONFIG_MESURE_INTERVAL = 10000;
constexpr const char* CONFIG_DEVICE_NAME = "semix";
constexpr uint8_t CONFIG_DS18B20_PIN = 4;         // GPIO du bus 1-Wire des sondes DS18B20
constexpr uint8_t CONFIG_DS18B20_RESOLUTION = 12; // 9 à 12 bits
