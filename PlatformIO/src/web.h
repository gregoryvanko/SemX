#pragma once
// Page de configuration (servie sur "/") : état envoyé et commandes reçues sur le WebSocket "/ws".

#include <Arduino.h>

// Send the current state and settings to every open configuration page
void broadcastState();

// Commands received from the configuration page (JSON messages on the WebSocket)
void handleConfigMessage(uint32_t clientId, const String &message);

// Refresh the configuration page (clock, relay states) every 2 s while it is open (to call from loop())
void webLoop();
