#include "devices.h"

#include "config.h"

SensorDS18B20 sondes(CONFIG_DS18B20_PIN);
SensorMoisture sol(CONFIG_MOISTURE_PIN);
RelayController relais_Pump(CONFIG_RELAY_Pump_PIN, true);
RelayController relais_Light(CONFIG_RELAY_Light_PIN, true);
