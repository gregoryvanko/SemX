#pragma once
// Relais qui simule l'appui sur un bouton poussoir marche / arrêt (lampes LED par exemple) :
// chaque changement d'état ferme le relais pendant pulseMs puis le rouvre.
//
// L'état des lampes ne peut pas être lu sur le relais (il est ouvert au repos dans les deux cas) :
// il est mémorisé et basculé à la fin de chaque impulsion. setActual() le corrige sans impulsion
// quand les lampes ne correspondent pas à l'état mémorisé.
//
// Les impulsions ne bloquent pas : loop() doit être appelé régulièrement. turnOn() / turnOff()
// fixent l'état voulu ; une impulsion est lancée tant que l'état mémorisé est différent, avec au moins
// gapMs de relais ouvert entre deux impulsions pour que la lampe voie deux appuis distincts.

#include <Arduino.h>
#include <functional>

#include "RelayController.h"

class PulseRelay {
public:
    PulseRelay(const char *name, uint8_t pin, bool activeLow = true, uint32_t pulseMs = 1000, uint32_t gapMs = 1000);

    // Relais ouvert ; initialOn : état des lampes au démarrage (aucune impulsion)
    void begin(bool initialOn);
    void loop();

    void turnOn();
    void turnOff();

    // Les lampes sont en réalité allumées (on = true) ou éteintes : corrige l'état mémorisé sans impulsion.
    // Refusé (false) pendant une impulsion.
    bool setActual(bool on);

    bool   isOn()           const;  // état mémorisé des lampes
    bool   target()         const;  // état demandé
    bool   isPulsing()      const;  // relais fermé en ce moment
    bool   isBusy()         const;  // impulsion en cours ou à venir
    String getStateString() const;

    // Appelé à chaque changement de l'état mémorisé (fin d'impulsion ou correction)
    void onChange(std::function<void(bool)> callback);

private:
    void request(bool on);
    void changed();

    const char     *_name;
    RelayController _relay;
    uint32_t        _pulseMs;
    uint32_t        _gapMs;
    bool            _on = false;
    bool            _target = false;
    bool            _pulsing = false;
    uint32_t        _pulseStart = 0;
    uint32_t        _released = 0;  // millis() de la dernière ouverture du relais
    std::function<void(bool)> _onChange;
};
