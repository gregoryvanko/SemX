#include "PulseRelay.h"

namespace {
const char *lampState(bool on) { return on ? "allumées" : "éteintes"; }
}  // namespace

PulseRelay::PulseRelay(const char *name, uint8_t pin, bool activeLow, uint32_t pulseMs, uint32_t gapMs)
    : _name(name), _relay(pin, activeLow), _pulseMs(pulseMs), _gapMs(gapMs) {}

void PulseRelay::begin(bool initialOn) {
    _relay.begin();
    _on = _target = initialOn;
    _pulsing = false;
    _released = millis();
    Serial.printf("[%s] Démarrage : lampes considérées %s (impulsion %lu ms)\n", _name, lampState(_on),
                  (unsigned long)_pulseMs);
}

void PulseRelay::loop() {
    if (_pulsing) {
        if (millis() - _pulseStart < _pulseMs) return;
        _relay.turnOff();
        _pulsing = false;
        _released = millis();
        _on = !_on;
        Serial.printf("[%s] Fin d'impulsion : relais ouvert, lampes %s\n", _name, lampState(_on));
        changed();
        return;
    }
    if (_on == _target || millis() - _released < _gapMs) return;
    Serial.printf("[%s] Impulsion pour %s : relais fermé pendant %lu ms\n", _name,
                  _target ? "allumer" : "éteindre", (unsigned long)_pulseMs);
    _pulsing = true;
    _pulseStart = millis();
    _relay.turnOn();
}

void PulseRelay::turnOn() { request(true); }
void PulseRelay::turnOff() { request(false); }

void PulseRelay::request(bool on) {
    if (_target == on) return;
    _target = on;
    if (_on == on && !_pulsing)
        Serial.printf("[%s] Demande : %s, lampes déjà %s\n", _name, on ? "allumer" : "éteindre", lampState(on));
    else
        Serial.printf("[%s] Demande : %s\n", _name, on ? "allumer" : "éteindre");
}

bool PulseRelay::setActual(bool on) {
    if (_pulsing) {
        Serial.printf("[%s] Correction refusée : impulsion en cours\n", _name);
        return false;
    }
    if (_on == on) return true;
    _on = on;
    Serial.printf("[%s] Correction sans impulsion : lampes %s en réalité\n", _name, lampState(on));
    changed();
    return true;
}

void PulseRelay::changed() {
    if (_onChange) _onChange(_on);
}

bool PulseRelay::isOn() const { return _on; }
bool PulseRelay::target() const { return _target; }
bool PulseRelay::isPulsing() const { return _pulsing; }
bool PulseRelay::isBusy() const { return _pulsing || _on != _target; }
String PulseRelay::getStateString() const { return _on ? "ON" : "OFF"; }

void PulseRelay::onChange(std::function<void(bool)> callback) { _onChange = callback; }
