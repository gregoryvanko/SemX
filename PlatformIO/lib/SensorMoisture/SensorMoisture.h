/*
 * SensorMoisture — lecture d'une sonde d'humidité du sol capacitive
 * « Capacitive Soil Moisture Sensor V1.2 » (AZDelivery) pour ESP32 (framework Arduino).
 *
 * La sonde délivre une tension analogique qui diminue quand l'humidité augmente.
 * measure() fait la moyenne de plusieurs lectures ADC, convertit le résultat en
 * pourcentage à partir de deux points de calibration (sonde à l'air / dans l'eau)
 * puis appelle le callback onMeasure().
 *
 * Voir README.md pour la description complète.
 */
#pragma once

#include <Arduino.h>
#include <functional>

#ifndef SENSORMOISTURE_MAX_SAMPLES
#define SENSORMOISTURE_MAX_SAMPLES 64
#endif

class SensorMoisture {
public:
  // Valeurs ADC (12 bits, atténuation 11 dB) typiques pour une sonde V1.2 alimentée en 3,3 V
  static constexpr uint16_t DEFAULT_DRY = 2800;  // sonde à l'air libre
  static constexpr uint16_t DEFAULT_WET = 1200;  // sonde plongée dans l'eau

  using MeasureCallback = std::function<void(const SensorMoisture &sensor)>;

  // pin : GPIO de l'ADC1 (32 à 39), l'ADC2 étant inutilisable lorsque le Wi-Fi est actif
  explicit SensorMoisture(uint8_t pin);

  // --- Cycle de vie ---------------------------------------------------------
  // samples : nombre de lectures ADC moyennées par mesure (1 à SENSORMOISTURE_MAX_SAMPLES)
  void begin(uint8_t samples = 16);

  // --- Réglages -------------------------------------------------------------
  // dry : valeur brute sonde à l'air (0 %), wet : valeur brute sonde dans l'eau (100 %)
  void setCalibration(uint16_t dry, uint16_t wet);
  uint16_t dry() const { return _dry; }
  uint16_t wet() const { return _wet; }
  void setSamples(uint8_t samples);
  uint8_t samples() const { return _samples; }

  // --- Mesure ---------------------------------------------------------------
  // Lit la sonde (≈ 1 ms pour 16 lectures) et appelle le callback. Retourne valid().
  bool measure();
  uint32_t lastMeasure() const { return _lastMeasure; }  // millis() de la dernière lecture
  void onMeasure(MeasureCallback cb) { _callback = cb; }

  // --- Résultats ------------------------------------------------------------
  uint16_t raw() const { return _raw; }               // moyenne brute de l'ADC (0 à 4095)
  uint32_t millivolts() const { return _millivolts; } // tension moyenne (corrigée par l'étalonnage eFuse)
  float percent() const { return _percent; }          // 0 à 100 %, NAN si la lecture est en erreur
  bool valid() const { return _valid; }               // false : sonde absente ou hors plage
  uint32_t errors() const { return _errors; }         // nombre de lectures en erreur consécutives
  // Ex. : {"raw":1850,"millivolts":1620,"percent":59.4,"valid":true}
  String toJson(uint8_t decimals = 1) const;

private:
  uint8_t _pin;
  uint8_t _samples = 16;
  uint16_t _dry = DEFAULT_DRY;
  uint16_t _wet = DEFAULT_WET;
  uint16_t _raw = 0;
  uint32_t _millivolts = 0;
  float _percent = NAN;
  bool _valid = false;
  uint32_t _errors = 0;
  uint32_t _lastMeasure = 0;
  MeasureCallback _callback;
};
