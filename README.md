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
- **Sonde TDS** : mesure la quantité de solides dissous dans l’eau du réservoir.

### Actionneurs

- **Relais pompe** : allume et éteint la pompe à eau.
- **Relais éclairage** : allume et éteint les lumières.

## Licence

Le projet est distribué sous licence Apache 2.0. Consulter le fichier [LICENSE](LICENSE) pour en connaître les conditions.
