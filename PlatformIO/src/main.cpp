#include <Arduino.h>
#include <ESPConnect.h>

// Page de démonstration servie sur /semis : échange de messages via le WebSocket /ws.
const char SEMIS_HTML[] PROGMEM = R"rawliteral(<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>SemiX</title></head><body>
<h1>SemiX</h1><p id="state">Connexion…</p>
<button onclick="ws.send('ping')">Envoyer ping</button><pre id="log"></pre>
<script>
const ws = new WebSocket('ws://' + location.host + '/ws');
ws.onopen = () => document.getElementById('state').textContent = 'Connecté';
ws.onclose = () => document.getElementById('state').textContent = 'Déconnecté';
ws.onmessage = e => document.getElementById('log').textContent += e.data + '\n';
</script></body></html>)rawliteral";

void setup() {
  Serial.begin(115200);

  espConnect.addRoute("/semis", HTTP_GET, SEMIS_HTML);

  espConnect.onWsMessage([](uint32_t clientId, const String &message) {
    if (message == "ping") espConnect.wsSend(clientId, "pong");
  });

  espConnect.onMqttMessage([](const String &topic, const String &payload) {
    Serial.printf("Message MQTT %s : %s\n", topic.c_str(), payload.c_str());
  });
  espConnect.subscribe("semix/cmd/#");

  espConnect.begin("semix", "SemiX-Setup");
}

void loop() {
  espConnect.loop();

  static uint32_t last = 0;
  if (espConnect.isMqttConnected() && millis() - last >= 30000) {
    last = millis();
    espConnect.publish("semix/uptime", millis() / 1000);
    espConnect.wsSend("uptime " + String(millis() / 1000) + " s");
  }
}
