#pragma once
// Mesures des sondes de température et d'humidité, et publication sur MQTT.

// Apply the stored names to the detected sensors (the id is used for sensors without a name)
void applySensorNames();

// Start the DS18B20 sensors and the soil moisture sensor
void sensorsBegin();

// Measure every settings.measureMs (to call from loop())
void sensorsLoop();
