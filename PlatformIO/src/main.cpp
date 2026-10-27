#include <Arduino.h>
#include <ESPConnect.h>
#include <SensorDS18B20.h>
#include <SensorMoisture.h>
#include <RelayController.h>
#include <time.h>
#include "config.h"

// Sondes DS18B20 sur le bus 1-Wire (résistance de tirage 4,7 kΩ vers 3,3 V)
SensorDS18B20 sondes(CONFIG_DS18B20_PIN);

// Sonde d'humidité du sol capacitive V1.2 (AOUT sur une broche de l'ADC1, alimentation 3,3 V)
SensorMoisture sol(CONFIG_MOISTURE_PIN);

// Contrôleur de relais
RelayController relais_Pump(CONFIG_RELAY_Pump_PIN, true);
RelayController relais_Light(CONFIG_RELAY_Light_PIN, true);

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

  // Start soil moisture sensor: percentage on "<device>/moisture/percent"
  // and full measurement as JSON on "<device>/moisture"
  sol.onMeasure([](const SensorMoisture &s) {
    String base = String(CONFIG_DEVICE_NAME) + "/moisture";
    if (s.valid()) {
      Serial.printf("Humidité du sol : %.1f %% (brut %u, %u mV)\n", s.percent(), s.raw(), s.millivolts());
      if (espConnect.isMqttConnected()) espConnect.publish(base + "/percent", s.percent(), false, 0, 1);
    }
  });
  sol.begin(CONFIG_MOISTURE_SAMPLES);
  sol.setCalibration(CONFIG_MOISTURE_DRY, CONFIG_MOISTURE_WET);

  // Start pump relay (off at startup)
  relais_Pump.begin();

  // Start light relay (off at startup)
  relais_Light.begin();

  // Start network time (NTP), synchronised as soon as WiFi is connected
  configTzTime(CONFIG_TIMEZONE, CONFIG_NTP_SERVER);
}

void loop() {
  espConnect.loop();
  sondes.loop();

  static uint32_t last = 0;
  if (millis() - last >= CONFIG_MESURE_INTERVAL) {
    last = millis();
    // Request a new measurement from the DS18B20 sensors
    sondes.requestMeasure();
    // Read the soil moisture sensor (synchronous, ≈ 1 ms)
    sol.measure();
  }

  // Pump cycle: on for CONFIG_PUMP_ON_DURATION, then off for CONFIG_PUMP_OFF_DURATION (non-blocking)
  static uint32_t pumpLast = millis();
  uint32_t pumpDuration = relais_Pump.isOn() ? CONFIG_PUMP_ON_DURATION : CONFIG_PUMP_OFF_DURATION;
  if (millis() - pumpLast >= pumpDuration) {
    pumpLast = millis();
    relais_Pump.toggle();
  }

  // Light schedule on network time: on every day at CONFIG_LIGHT_START_HOUR:MINUTE
  // for CONFIG_LIGHT_ON_DURATION, off the rest of the day.
  // The light stays off until the time is synchronised.
  static uint32_t lightLast = 0;
  if (millis() - lightLast >= 1000) {
    lightLast = millis();
    struct tm now;
    if (getLocalTime(&now, 0)) {
      const int32_t start = CONFIG_LIGHT_START_HOUR * 3600 + CONFIG_LIGHT_START_MINUTE * 60;
      const int32_t secondsOfDay = now.tm_hour * 3600 + now.tm_min * 60 + now.tm_sec;
      const uint32_t elapsed = (secondsOfDay - start + 86400) % 86400;
      const bool lightOn = elapsed < CONFIG_LIGHT_ON_DURATION / 1000;
      if (lightOn != relais_Light.isOn()) lightOn ? relais_Light.turnOn() : relais_Light.turnOff();
    }
  }
}
