# SemiX

SemiX est un projet de chambre de culture destiné à accompagner la germination et les premières étapes de croissance des semis. L’objectif est de réunir dans un espace contrôlé les conditions dont les jeunes plants ont besoin, et de rendre leur suivi plus régulier qu’avec une installation entièrement manuelle.

## Objectifs

La chambre de culture vise à agir sur plusieurs paramètres importants pour le développement des semis :

- **L’éclairage** : fournir une durée et une période d’éclairage adaptées aux besoins des plants.
- **L’arrosage** : apporter de l’eau de manière maîtrisée afin de maintenir un substrat suffisamment humide, sans l’inonder.
- **La température** : suivre et réguler la température de l’espace de culture pour limiter les variations défavorables à la germination.
- **La chaleur** : prévoir une source de chaleur si nécessaire, pilotée en fonction des conditions mesurées.
- **L’humidité** : surveiller l’humidité de l’air et, selon la conception retenue, contribuer à la maintenir dans une plage appropriée.

## Éléments techniques

### Contrôleur

- **ESP32** : microcontrôleur chargé de piloter l’ensemble du système (lecture des capteurs et commande des actionneurs).

### Capteurs

- **Sonde de température DS18B20 (réservoir)** : mesure la température de l’eau du réservoir.
- **Sonde de température DS18B20 (semis)** : mesure la température au niveau du semis.
- **Capteur d’humidité du sol (moisture sensor)** : mesure l’humidité du substrat des semis.

### Actionneurs

- **Relais pompe** : allume et éteint la pompe à eau.
- **Relais éclairage** : allume et éteint les lumières.

### Brochage

| Élément | Broche signal | Alimentation | Remarque |
|---|---|---|---|
| DS18B20 réservoir | GPIO4 | 3V3 / GND | Bus 1-Wire partagé |
| DS18B20 semis | GPIO4 | 3V3 / GND | Une seule résistance de 4,7 kΩ entre DATA et 3V3 pour tout le bus |
| Capteur d’humidité du sol | GPIO34 | 3V3 / GND | Modèle capacitif recommandé |
| Relais pompe | GPIO26 (IN) | 5V / GND | Pompe branchée sur COM/NO, avec sa propre alimentation |
| Relais éclairage | GPIO27 (IN) | 5V / GND | Lumières branchées sur COM/NO |
| Alimentation 5 V | VIN / 5V de l’ESP32 | 220v | Toutes les masses (GND) reliées entre elles |

Remarques :

- GPIO34 et GPIO35 appartiennent à l’ADC1, qui reste utilisable lorsque le Wi-Fi est actif (contrairement à l’ADC2).
- GPIO4, GPIO26 et GPIO27 ne sont pas des broches de démarrage, ce qui évite un blocage au boot ou un déclenchement intempestif des relais.
- Les DS18B20 acceptent de 3,0 à 5,5 V. Si elles sont alimentées en 5 V, la résistance de tirage doit rester reliée au 3V3, car les GPIO de l’ESP32 ne tolèrent pas le 5 V.
- De nombreux modules relais sont actifs à l’état bas : vérifier la logique du module utilisé et sa compatibilité avec une commande en 3,3 V.

## Licence

Le projet est distribué sous licence Apache 2.0. Consulter le fichier [LICENSE](LICENSE) pour en connaître les conditions.
