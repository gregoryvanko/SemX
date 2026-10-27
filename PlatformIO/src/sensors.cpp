#include "sensors.h"

#include <ArduinoJson.h>
#include <ESPConnect.h>

#include "config.h"
#include "devices.h"
#include "relays.h"
#include "settings.h"
#include "web.h"

void applySensorNames() {
  for (const SensorDS18B20::Sensor &sonde : sondes.sensors()) {
    String name = sensorNames.get(sonde.id);
    sondes.setName(sonde.id, name.isEmpty() ? sonde.id : name);
  }
}

void sensorsBegin() {
  // Start DS18B20 sensors: one value per named sensor on "<device>/temperature/<name>"
  // and all named sensors as JSON on "<device>/temperature".
  // Sensors without a name are not published.
  sondes.onMeasure([](const SensorDS18B20 &s) {
    String base = espConnect.deviceName() + "/temperature";
    JsonDocument doc;
    JsonArray list = doc.to<JsonArray>();
    for (const SensorDS18B20::Sensor &sonde : s.sensors()) {
      String name = sensorNames.get(sonde.id);
      if (!sonde.valid) continue;
      Serial.printf("%s : %.2f °C\n", sonde.name.c_str(), sonde.temperature);
      if (name.isEmpty()) continue;
      if (espConnect.isMqttConnected()) espConnect.publish(base + "/" + name, sonde.temperature);
      JsonObject o = list.add<JsonObject>();
      o["id"] = sonde.id;
      o["name"] = name;
      o["temperature"] = serialized(String(sonde.temperature, 2));
    }
    if (espConnect.isMqttConnected() && list.size() > 0) {
      String json;
      serializeJson(doc, json);
      espConnect.publish(base, json);
    }
    broadcastState();
  });
  sondes.begin(CONFIG_DS18B20_RESOLUTION);
  applySensorNames();

  // Start soil moisture sensor: percentage on "<device>/moisture/percent"
  sol.onMeasure([](const SensorMoisture &s) {
    updateSoilDry();
    String base = espConnect.deviceName() + "/moisture";
    if (s.valid()) {
      Serial.printf("Humidité du sol : %.1f %% (brut %u, %u mV)\n", s.percent(), s.raw(), s.millivolts());
      if (espConnect.isMqttConnected()) espConnect.publish(base + "/percent", s.percent(), false, 0, 1);
    }
  });
  sol.begin(CONFIG_MOISTURE_SAMPLES);
  sol.setCalibration(settings.moistureDry, settings.moistureWet);
}

void sensorsLoop() {
  sondes.loop();

  static uint32_t last = 0;
  if (millis() - last >= settings.measureMs) {
    last = millis();
    // New sensors may have been found by a rescan: give them their stored names
    applySensorNames();
    // Request a new measurement from the DS18B20 sensors
    sondes.requestMeasure();
    // Read the soil moisture sensor (synchronous, ≈ 1 ms)
    sol.measure();
  }
}
