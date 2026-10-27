#pragma once
// Matériel : sondes et relais.

#include <RelayController.h>
#include <SensorDS18B20.h>
#include <SensorMoisture.h>

// Sondes DS18B20 sur le bus 1-Wire (résistance de tirage 4,7 kΩ vers 3,3 V)
extern SensorDS18B20 sondes;

// Sonde d'humidité du sol capacitive V1.2 (AOUT sur une broche de l'ADC1, alimentation 3,3 V)
extern SensorMoisture sol;

// Contrôleur de relais
extern RelayController relais_Pump;
extern RelayController relais_Light;
