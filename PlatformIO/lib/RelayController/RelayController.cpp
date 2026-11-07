#include "RelayController.h"

RelayController::RelayController(uint8_t pin, bool activeLow)
    : _pin(pin), _activeLow(activeLow), _state(false) {}

void RelayController::begin() {
    pinMode(_pin, OUTPUT);
    turnOff();
    Serial.printf("[Relay GPIO%u] Initialisé\n", _pin);
}

void RelayController::turnOn() {
    _state = true;
    digitalWrite(_pin, _activeLow ? LOW : HIGH);
    Serial.printf("[Relay GPIO%u] Fermé (ON)\n", _pin);
}

void RelayController::turnOff() {
    _state = false;
    digitalWrite(_pin, _activeLow ? HIGH : LOW);
    Serial.printf("[Relay GPIO%u] Ouvert (OFF)\n", _pin);
}

void RelayController::toggle() {
    _state ? turnOff() : turnOn();
}

void RelayController::pulse(uint32_t durationMs) {
    turnOn();
    delay(durationMs);
    turnOff();
}

bool RelayController::isOn() const {
    return _state;
}

String RelayController::getStateString() const {
    return _state ? "ON" : "OFF";
}