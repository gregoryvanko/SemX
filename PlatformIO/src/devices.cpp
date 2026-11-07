#include "devices.h"

#include "config.h"

SensorDS18B20 sondes(CONFIG_DS18B20_PIN);
SensorMoisture sol(CONFIG_MOISTURE_PIN);
RelayController relais_Pump(CONFIG_RELAY_Pump_PIN, false);
PulseRelay relais_Light("Éclairage", CONFIG_RELAY_Light_PIN, false, CONFIG_LIGHT_PULSE_MS, CONFIG_LIGHT_PULSE_GAP_MS);