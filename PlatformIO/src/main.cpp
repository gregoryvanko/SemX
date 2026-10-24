#include <Arduino.h>
#include <ESPConnect.h>
#include <SensorDS18B20.h>
#include "config.h"

// Sondes DS18B20 sur le bus 1-Wire (résistance de tirage 4,7 kΩ vers 3,3 V)
SensorDS18B20 sondes(CONFIG_DS18B20_PIN);


void setup() {
  Serial.begin(CONFIG_BAUDRATE);

  // Setup onReceive callback for WebSocket messages
  espConnect.onWsMessage([](uint32_t clientId, const String &message) {
    if (message == "ping") espConnect.wsSend(clientId, "pong");
  });

  // Setup onMqttMessage callback for MQTT messages
  espConnect.onMqttMessage([](const String &topic, const String &payload) {
    Serial.printf("Message MQTT %s : %s\n", topic.c_str(), payload.c_str());
  });

  // Subscribe to MQTT topic "semix/cmd/#" to receive commands
  espConnect.subscribe(String(CONFIG_DEVICE_NAME) + "/cmd/#");

  // Enable OTA updates with the password "gregory"
  espConnect.enableOTA("gregory");

  // Start ESPConnect with device name "semix" and AP name "SemiX-Setup"
  espConnect.begin(CONFIG_DEVICE_NAME, "SemiX-Setup");

  // Start DS18B20 sensors: one value per sensor on "<device>/temperature/<id>"
  // and all sensors as JSON on "<device>/temperature"
  sondes.onMeasure([](const SensorDS18B20 &s) {
    String base = String(CONFIG_DEVICE_NAME) + "/temperature";
    for (const SensorDS18B20::Sensor &sonde : s.sensors()) {
      if (sonde.valid) {
        Serial.printf("%s : %.2f °C\n", sonde.name.c_str(), sonde.temperature);
        if (espConnect.isMqttConnected()) espConnect.publish(base + "/" + sonde.id, sonde.temperature);
      }
    }
    espConnect.publish(base, s.toJson());
  });
  sondes.begin(CONFIG_DS18B20_RESOLUTION);
}

void loop() {
  espConnect.loop();
  sondes.loop();

  static uint32_t last = 0;
  if (millis() - last >= CONFIG_MESURE_INTERVAL) {
    last = millis();
    // Request a new measurement from the DS18B20 sensors
    sondes.requestMeasure();
  }
}
