#include <Arduino.h>
#include <ESPConnect.h>
#include "config.h"


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
}

void loop() {
  espConnect.loop();

  static uint32_t last = 0;
  if (millis() - last >= CONFIG_MESURE_INTERVAL) {
    last = millis();
  }
}
