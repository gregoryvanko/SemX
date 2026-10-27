#include <Arduino.h>
#include <ESPConnect.h>
#include <time.h>
#include "config.h"
#include "config_page.h"
#include "relays.h"
#include "sensors.h"
#include "settings.h"
#include "web.h"

void setup() {
  Serial.begin(CONFIG_BAUDRATE);

  // Load the settings saved from the configuration page (defaults from config.h)
  settings.load();

  // WebSocket messages: commands from the configuration page
  espConnect.onWsMessage(handleConfigMessage);

  // MQTT messages: relay commands on "<device>/cmd/pump" and "<device>/cmd/light"
  // ("<device>" : device name set on /status; subscription done by relaysLoop())
  espConnect.onMqttMessage(handleMqttMessage);

  // Enable OTA updates with the password "gregory"
  espConnect.enableOTA("gregory");

  // Configuration page (sensor names, measurements, moisture calibration, pump and light)
  espConnect.addRoute("/", HTTP_GET, SEMX_HTML);

  // Start ESPConnect with device name "semix" and AP name "SemiX-Setup"
  espConnect.begin(CONFIG_DEVICE_NAME, "SemiX-Setup");

  // Start the temperature and soil moisture sensors
  sensorsBegin();

  // Start the pump and light relays (off at startup)
  relaysBegin();

  // Start network time (NTP), synchronised as soon as WiFi is connected
  configTzTime(CONFIG_TIMEZONE, CONFIG_NTP_SERVER);
}

void loop() {
  espConnect.loop();
  // Measurements every settings.measureMs
  sensorsLoop();
  // Pump cycle / watering, light schedule, relay states on MQTT
  relaysLoop();
  // Refresh the configuration page while it is open
  webLoop();
}
