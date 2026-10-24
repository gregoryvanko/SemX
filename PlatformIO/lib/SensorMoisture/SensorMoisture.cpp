#include "SensorMoisture.h"

#ifdef SENSORMOISTURE_NO_LOG
#define SM_LOG(...) \
  do {              \
  } while (0)
#else
#define SM_LOG(fmt, ...) Serial.printf("[SensorMoisture] " fmt "\n", ##__VA_ARGS__)
#endif

// En dessous / au-dessus de ces valeurs brutes, la sonde est considérée absente ou en court-circuit :
// la sortie d'une V1.2 reste comprise entre ≈ 1000 (eau) et ≈ 3000 (air) sous 3,3 V.
static constexpr uint16_t RAW_MIN = 100;
static constexpr uint16_t RAW_MAX = 4000;

SensorMoisture::SensorMoisture(uint8_t pin) : _pin(pin) {}

void SensorMoisture::begin(uint8_t samples) {
  setSamples(samples);
  analogReadResolution(12);
  analogSetPinAttenuation(_pin, ADC_11db);  // plage de mesure 0 à ≈ 3,1 V
  pinMode(_pin, INPUT);
  SM_LOG("GPIO %u, calibration air %u / eau %u, %u lectures par mesure", _pin, _dry, _wet, _samples);
}

void SensorMoisture::setCalibration(uint16_t dry, uint16_t wet) {
  if (dry == wet) return;  // calibration impossible
  _dry = dry;
  _wet = wet;
}

void SensorMoisture::setSamples(uint8_t samples) {
  _samples = constrain(samples, 1, SENSORMOISTURE_MAX_SAMPLES);
}

bool SensorMoisture::measure() {
  uint32_t rawSum = 0;
  uint32_t mvSum = 0;
  for (uint8_t i = 0; i < _samples; i++) {
    rawSum += analogRead(_pin);
    mvSum += analogReadMilliVolts(_pin);
    delayMicroseconds(50);
  }
  _raw = rawSum / _samples;
  _millivolts = mvSum / _samples;
  _lastMeasure = millis();

  if (_raw < RAW_MIN || _raw > RAW_MAX) {
    _valid = false;
    _percent = NAN;
    _errors++;
    SM_LOG("Lecture en erreur : valeur brute %u hors plage (sonde débranchée ?)", _raw);
  } else {
    // Interpolation linéaire entre les deux points de calibration (dry > wet en général)
    float p = 100.0f * ((float)_dry - _raw) / ((float)_dry - _wet);
    _percent = constrain(p, 0.0f, 100.0f);
    _valid = true;
    _errors = 0;
  }

  if (_callback) _callback(*this);
  return _valid;
}

String SensorMoisture::toJson(uint8_t decimals) const {
  String json = "{\"raw\":" + String(_raw) + ",\"millivolts\":" + String(_millivolts) + ",\"percent\":";
  json += _valid ? String(_percent, (unsigned int)decimals) : String("null");
  json += ",\"valid\":";
  json += _valid ? "true" : "false";
  json += '}';
  return json;
}
