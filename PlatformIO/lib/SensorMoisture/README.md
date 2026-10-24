# SensorMoisture

Librairie ESP32 (framework Arduino, PlatformIO) pour lire une sonde d'humidité du sol capacitive **Capacitive Soil Moisture Sensor V1.2** (AZDelivery) :

- moyenne de plusieurs lectures ADC pour lisser le bruit ;
- conversion en **pourcentage d'humidité** à partir de deux points de calibration (sonde à l'air / dans l'eau) ;
- tension en millivolts corrigée par l'étalonnage d'usine de l'ADC (eFuse) ;
- détection des erreurs de lecture (sonde débranchée, court-circuit) ;
- callback après chaque mesure et export JSON.

Aucune dépendance externe.

## Principe

La sonde V1.2 est capacitive : elle ne s'oxyde pas comme les sondes résistives. Elle délivre une tension analogique qui **diminue quand l'humidité augmente** (≈ 2,5 V à l'air, ≈ 1,1 V dans l'eau sous 3,3 V). La librairie convertit linéairement la valeur brute de l'ADC entre deux points :

```
percent = 100 × (dry − raw) / (dry − wet)     borné entre 0 et 100 %
```

## Câblage

| Sonde V1.2   | ESP32                                  |
|--------------|----------------------------------------|
| GND (noir)   | GND                                    |
| VCC (rouge)  | 3,3 V                                  |
| AOUT (jaune) | GPIO de l'ADC1 (ex. GPIO 34)           |

- Utiliser **obligatoirement une broche de l'ADC1** (GPIO 32 à 39) : l'ADC2 n'est pas disponible lorsque le Wi-Fi est actif.
- Alimenter la sonde en **3,3 V** : sous 5 V sa sortie peut dépasser la plage de mesure de l'ESP32 (≈ 3,1 V avec une atténuation de 11 dB).
- Enfoncer la sonde jusqu'au trait blanc seulement ; l'électronique en haut du circuit n'est pas étanche.

## Calibration

Les valeurs par défaut (`dry = 2800`, `wet = 1200`) varient d'une sonde à l'autre. Pour calibrer :

1. Laisser la sonde à l'air sec, noter `raw()` → valeur `dry`.
2. Plonger la sonde dans un verre d'eau (jusqu'au trait), noter `raw()` → valeur `wet`.
3. Appeler `setCalibration(dry, wet)` après `begin()`.

Refaire la calibration si la longueur du câble ou la tension d'alimentation change.

## Exemple

```cpp
#include <Arduino.h>
#include <SensorMoisture.h>

SensorMoisture sol(34);  // sortie AOUT sur GPIO 34

void setup() {
  Serial.begin(115200);

  sol.onMeasure([](const SensorMoisture &s) {
    if (s.valid()) Serial.printf("Humidité : %.1f %% (brut %u, %u mV)\n", s.percent(), s.raw(), s.millivolts());
    Serial.println(s.toJson());
  });

  sol.begin(16);                   // 16 lectures moyennées par mesure
  sol.setCalibration(2750, 1180);  // valeurs relevées à l'air et dans l'eau
}

void loop() {
  static uint32_t last = 0;
  if (millis() - last >= 10000) {
    last = millis();
    sol.measure();
  }
}
```

## API

### Cycle de vie et réglages

| Méthode | Description |
|---|---|
| `SensorMoisture(uint8_t pin)` | Associe la sonde à la broche `pin` (ADC1 : GPIO 32 à 39). |
| `void begin(uint8_t samples = 16)` | Configure l'ADC (12 bits, atténuation 11 dB) et le nombre de lectures moyennées. |
| `void setCalibration(uint16_t dry, uint16_t wet)` | Valeurs brutes correspondant à 0 % (air) et 100 % (eau). Ignoré si `dry == wet`. |
| `uint16_t dry()` / `uint16_t wet()` | Calibration actuelle. |
| `void setSamples(uint8_t samples)` | Nombre de lectures moyennées, de 1 à `SENSORMOISTURE_MAX_SAMPLES`. |

### Mesure

| Méthode | Description |
|---|---|
| `bool measure()` | Lit la sonde, met à jour les résultats et appelle le callback. Retourne `valid()`. Durée ≈ 1 ms pour 16 lectures. |
| `uint32_t lastMeasure()` | `millis()` de la dernière lecture. |
| `void onMeasure(MeasureCallback cb)` | Callback `void(const SensorMoisture &)` appelé à la fin de chaque `measure()`. |

### Résultats

| Méthode | Description |
|---|---|
| `uint16_t raw()` | Moyenne brute de l'ADC (0 à 4095). |
| `uint32_t millivolts()` | Tension moyenne en mV. |
| `float percent()` | Humidité de 0 à 100 %, `NAN` si la lecture est en erreur. |
| `bool valid()` | `false` si la valeur brute est hors plage (< 100 ou > 4000) : sonde débranchée ou en court-circuit. |
| `uint32_t errors()` | Nombre de lectures en erreur consécutives. |
| `String toJson(uint8_t decimals = 1)` | `{"raw":1850,"millivolts":1620,"percent":59.4,"valid":true}` (`percent` vaut `null` en cas d'erreur). |

## Options de compilation

| Macro | Défaut | Description |
|---|---|---|
| `SENSORMOISTURE_MAX_SAMPLES` | `64` | Nombre maximum de lectures moyennées par mesure. |
| `SENSORMOISTURE_NO_LOG` | — | Désactive les messages sur le port série. |

À définir dans `platformio.ini`, par exemple : `build_flags = -DSENSORMOISTURE_NO_LOG`.

## Remarques

- Une entrée ADC laissée en l'air peut renvoyer des valeurs aléatoires dans la plage valide : la détection d'une sonde débranchée n'est fiable qu'avec une résistance de rappel (ex. 100 kΩ vers GND) sur l'entrée.
- La relation entre tension et humidité n'est pas parfaitement linéaire ; le pourcentage est une indication relative, utile pour comparer et déclencher un arrosage, pas une mesure volumétrique.
- Plusieurs sondes : créer une instance `SensorMoisture` par broche.
