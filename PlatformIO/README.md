# SemX — firmware ESP32

Firmware d'un ESP32 qui surveille et pilote un semis ou une petite culture :

- mesure de la **température** (une ou plusieurs sondes DS18B20) et de l'**humidité du sol** (sonde capacitive) ;
- pilotage d'une **pompe** d'arrosage (cycle marche / arrêt, ou selon l'humidité du sol) ;
- pilotage d'un **éclairage** à heure fixe, sur l'heure réseau ;
- page web **SemX** pour tout régler, avec enregistrement des réglages en mémoire ;
- publication des mesures et de l'état des relais sur **MQTT**, et commande des relais par MQTT.

## Matériel

Carte : **AZ-Delivery DevKit V4** (ESP32).

| Élément | GPIO | Constante (`config.h`) | Remarque |
|---|---|---|---|
| Bus 1-Wire des sondes DS18B20 | 4 | `CONFIG_DS18B20_PIN` | résistance de tirage 4,7 kΩ vers 3,3 V |
| Sonde d'humidité capacitive V1.2 (AOUT) | 34 | `CONFIG_MOISTURE_PIN` | broche de l'ADC1 (32 à 39) obligatoire, alimentation 3,3 V |
| Relais de la pompe | 26 | `CONFIG_RELAY_Pump_PIN` | relais actif à l'état bas |
| Relais de l'éclairage | 27 | `CONFIG_RELAY_Light_PIN` | relais actif à l'état bas |
| Bouton BOOT | 0 | — | appui de 2 s : efface le WiFi (voir plus bas) |

## Compilation et téléversement

Le projet utilise PlatformIO ([platformio.ini](platformio.ini)) avec deux environnements :

| Environnement | Téléversement |
|---|---|
| `az-delivery-devkit-v4` | par le câble USB |
| `az-delivery-devkit-v4_ota` | par le réseau (OTA), vers `ESP-SemiX.rix`, mot de passe `gregory` |

```bash
pio run -e az-delivery-devkit-v4 -t upload
```

```bash
pio run -e az-delivery-devkit-v4_ota -t upload
```

Bibliothèques téléchargées automatiquement : AsyncTCP, ESPAsyncWebServer, OneWire, DallasTemperature et ArduinoJson. Les bibliothèques du projet sont dans [lib/](lib/) (voir plus bas).

## Premier démarrage et connexion WiFi

La connexion est gérée par la bibliothèque [ESPConnect](lib/ESPConnect/README.md).

1. Sans réseau WiFi enregistré, l'ESP32 ouvre le point d'accès **SemiX-Setup** (sans mot de passe).
2. En s'y connectant, une page s'ouvre (sinon : `http://192.168.1.1`) pour choisir le réseau WiFi et saisir son mot de passe.
3. L'ESP32 redémarre et se connecte à ce réseau.

Un appui de 2 s sur le bouton BOOT efface le réseau enregistré et rouvre le point d'accès.

Une fois connecté, l'ESP32 sert deux pages :

| Adresse | Page |
|---|---|
| `http://<adresse-de-l-esp32>/` | page **SemX** : réglages et état en direct |
| `http://<adresse-de-l-esp32>/status` | page de statut d'ESPConnect : WiFi, MQTT, nom d'appareil, OTA |

La configuration du broker MQTT se fait sur la page `/status`.

## Fonctionnement

### Mesures

Toutes les sondes sont lues à intervalle régulier : **10 s** par défaut, réglable de 2 s à 1 h sur la page SemX.

- **Températures** : toutes les sondes DS18B20 présentes sur le bus sont détectées automatiquement (16 au maximum). Chaque sonde est reconnue par son identifiant unique (16 caractères hexadécimaux) et peut recevoir un **nom** sur la page SemX. **Une sonde sans nom n'est pas publiée sur MQTT.** Le bouton « Rechercher les sondes » relance la détection après un branchement.
- **Humidité du sol** : la valeur brute de l'ADC (0 à 4095) est convertie en pourcentage à partir de deux points de calibration : la valeur « sec » (sonde à l'air, 0 %) et la valeur « humide » (sonde dans l'eau, 100 %). La calibration se fait sur la page SemX grâce aux boutons « Valeur actuelle ».

### Pompe

La pompe a quatre modes, choisis sur la page SemX ou par MQTT :

| Mode | Fonctionnement |
|---|---|
| **Automatique** | Cycle sans fin : arrêt pendant la durée d'arrêt, puis marche pendant la durée de marche (de 1 s à 24 h chacune). Le cycle commence par la période d'arrêt. |
| **Humidité** | La pompe démarre quand l'humidité passe sous le **seuil bas** (40 % par défaut) et s'arrête dès que le **seuil haut** est atteint (80 % par défaut), sans suivre le cycle. Après un redémarrage, ou quand on choisit ce mode, la pompe démarre si l'humidité est sous le seuil haut. Sans lecture valide de la sonde, la pompe reste arrêtée. |
| **Marche forcée** | Pompe allumée en permanence. |
| **Arrêt forcé** | Pompe éteinte en permanence. |

Le choix entre Automatique et Humidité est enregistré et conservé après un redémarrage. Les modes forcés ne le sont pas : après un redémarrage, la pompe repart dans son dernier mode automatique. Ainsi, une pompe oubliée en marche forcée ne tourne pas sans fin après une coupure de courant.

En mode Humidité, la pompe réagit au plus tard un intervalle de mesure après le passage d'un seuil.

### Éclairage

| Mode | Fonctionnement |
|---|---|
| **Automatique** | Allumage chaque jour à l'**heure d'allumage** (6 h 00 par défaut) pendant la **durée d'allumage** (16 h par défaut, 24 h au maximum), puis extinction jusqu'au lendemain. La plage peut passer minuit (par exemple de 20 h à 6 h). |
| **Marche forcée** / **Arrêt forcé** | Éclairage allumé ou éteint en permanence, non conservé après un redémarrage. |

L'heure vient d'Internet (NTP, serveur `pool.ntp.org`), dans le fuseau de **Bruxelles**, avec passage automatique à l'heure d'été. Tant que l'heure n'est pas reçue, l'éclairage reste éteint. Après un redémarrage, il reprend directement l'état qui correspond à l'heure.

## Page SemX

La page `/` est découpée en cartes repliables. Leur titre reste visible quand elles sont fermées et affiche un résumé : nombre de sondes, intervalle de mesure, humidité, état de la pompe et de l'éclairage.

| Carte | Contenu |
|---|---|
| Sondes de température | température de chaque sonde, champ pour son nom, recherche des sondes |
| Mesures | intervalle de mesure |
| Humidité du sol | pourcentage, valeur brute et tension, lecture immédiate, calibration « sec » / « humide » |
| Pompe | choix du mode, durées du cycle, seuils du mode Humidité, état de l'arrosage |
| Éclairage | choix du mode, heure et durée d'allumage, heure d'extinction calculée |

- **Enregistrement automatique** : chaque réglage est enregistré dès qu'on quitte le champ ou qu'on appuie sur Entrée. Un bandeau vert confirme « Enregistré. ».
- **Valeur refusée** : un bandeau rouge reste affiché et le champ garde ce qui a été tapé, jusqu'à ce qu'une saisie valide soit enregistrée.
- **Valeurs par défaut** : le bouton « Revenir aux valeurs par défaut » remet les valeurs de `config.h`. Les noms des sondes sont conservés.
- **Échanges avec l'ESP32** : la page communique par WebSocket et se met à jour toutes les 2 s, et à chaque changement d'état.
- **Mémoire du navigateur** : les cartes ouvertes sont mémorisées dans le navigateur.

La page n'est pas protégée par mot de passe : tout appareil du réseau local peut y accéder et modifier les réglages.

### Journal série

Tous les échanges avec la page SemX sont écrits sur le port série (115200 bauds), avec le préfixe `[SemX]` et le numéro du client WebSocket :

```text
[SemX] #3 → {"cmd":"mode","relay":"pump","mode":"moisture"}
[SemX] #3 : pompe en mode moisture
[SemX] #3 → {"cmd":"save","measure":10,"dry":2800,…}
[SemX] #3 : réglages enregistrés — mesure toutes les 10 s, pompe marche 10 s / arrêt 1 min, humidité 40 % → 80 %, éclairage 06:00 pendant 16 h, calibration sec 2800 / humide 1200
[SemX] #3 ← OK Enregistré.
```

| Ligne | Signification |
|---|---|
| `→` | message reçu de la page |
| `:` | action réalisée (ou message ignoré, avec la raison) |
| `←` | réponse envoyée à la page (`OK` ou `ERREUR` suivi du message affiché) |

Le rafraîchissement automatique de l'état toutes les 2 s n'est pas journalisé. Les connexions et déconnexions des clients WebSocket sont journalisées par ESPConnect.

## MQTT

Le préfixe des topics est le **nom d'appareil** réglé sur la page `/status` (`semix` par défaut, valeur de `CONFIG_DEVICE_NAME`). Les exemples ci-dessous utilisent `semix`.

### Publiés par l'ESP32

| Topic | Contenu | Retenu |
|---|---|---|
| `semix/temperature/<nom>` | température d'une sonde nommée, en °C (2 décimales) | non |
| `semix/temperature` | JSON des sondes nommées : `[{"id":"28FF…","name":"serre","temperature":21.50}]` | non |
| `semix/moisture/percent` | humidité du sol en % (1 décimale) | non |
| `semix/pump/state` | `ON` / `OFF` | oui |
| `semix/pump/mode` | `auto` / `moisture` / `on` / `off` | oui |
| `semix/light/state` | `ON` / `OFF` | oui |
| `semix/light/mode` | `auto` / `on` / `off` | oui |
| `semix/status` | `online` toutes les 60 s ; `offline` en cas de déconnexion (testament) | oui |

Les températures et l'humidité sont publiées à chaque mesure. L'état et le mode des relais sont publiés à chaque changement et à chaque reconnexion au broker.

### Commandes reçues

| Topic | Message |
|---|---|
| `semix/cmd/pump` | `auto`, `moisture`, `on` ou `off` |
| `semix/cmd/light` | `auto`, `on` ou `off` |

Les majuscules sont acceptées. Une commande MQTT a le même effet que les boutons de la page SemX.

**Ne pas envoyer de commande en mode « retenu »** : le broker la renverrait à chaque reconnexion.

```bash
mosquitto_pub -h <broker> -t semix/cmd/pump -m on
```

Quand le nom d'appareil change sur `/status`, sans redémarrage :

- la connexion MQTT est relancée et tous les topics passent sous le nouveau nom ;
- l'abonnement aux commandes passe à `<nouveau nom>/cmd/#` ;
- l'état et le mode des relais sont republiés sous le nouveau nom ;
- les messages retenus de l'ancien nom (`pump/state`, `pump/mode`, `light/state`, `light/mode`) sont effacés du broker.

## Réglages et mémoire

Les constantes de [src/config.h](src/config.h) sont les **valeurs par défaut**. Les valeurs modifiées sur la page SemX sont enregistrées dans la mémoire NVS de l'ESP32 et ont priorité après un redémarrage.

| Réglage | Constante par défaut | Valeur |
|---|---|---|
| Intervalle de mesure | `CONFIG_MESURE_INTERVAL` | 10 s |
| Calibration humidité « sec » / « humide » | `CONFIG_MOISTURE_DRY` / `CONFIG_MOISTURE_WET` | 2800 / 1200 |
| Marche / arrêt de la pompe (mode Automatique) | `CONFIG_PUMP_ON_DURATION` / `CONFIG_PUMP_OFF_DURATION` | 10 s / 60 s |
| Mode automatique de la pompe | `CONFIG_PUMP_MOISTURE_ENABLED` | `false` (cycle) |
| Seuils du mode Humidité | `CONFIG_PUMP_MOISTURE_LOW` / `CONFIG_PUMP_MOISTURE_HIGH` | 40 % / 80 % |
| Heure d'allumage de l'éclairage | `CONFIG_LIGHT_START_HOUR` / `CONFIG_LIGHT_START_MINUTE` | 6 h 00 |
| Durée d'allumage de l'éclairage | `CONFIG_LIGHT_ON_DURATION` | 16 h |

Ne se règlent que dans `config.h` : les broches, la résolution des DS18B20 (12 bits), le nombre de lectures moyennées pour l'humidité (16), le fuseau horaire et le serveur NTP. Le nom d'appareil se change sur la page `/status`.

Espaces NVS utilisés :

| Espace | Contenu |
|---|---|
| `semix` | réglages de la page SemX |
| `semix_ds` | noms des sondes de température |
| `espc_wifi`, `espc_mqtt`, `espc_dev` | WiFi, broker MQTT et nom d'appareil (ESPConnect) |

Un réglage enregistré incohérent est ignoré au démarrage, et les valeurs par défaut sont alors utilisées.

## Organisation du code

### `src/`

| Fichier | Rôle |
|---|---|
| [main.cpp](src/main.cpp) | `setup()` et `loop()` seulement : démarrage des modules et appel de leurs boucles |
| [config.h](src/config.h) | broches et valeurs par défaut |
| [devices.h](src/devices.h) / [.cpp](src/devices.cpp) | objets matériels : `sondes`, `sol`, `relais_Pump`, `relais_Light` |
| [settings.h](src/settings.h) / [.cpp](src/settings.cpp) | réglages modifiables (`settings`) et noms des sondes (`sensorNames`) : lecture, enregistrement en NVS, vérification |
| [sensors.h](src/sensors.h) / [.cpp](src/sensors.cpp) | mesures périodiques, noms des sondes, publication des mesures sur MQTT |
| [relays.h](src/relays.h) / [.cpp](src/relays.cpp) | modes des relais, cycle et arrosage de la pompe, horaire de l'éclairage, état et commandes MQTT |
| [web.h](src/web.h) / [.cpp](src/web.cpp) | page SemX côté ESP32 : état envoyé, commandes reçues, rafraîchissement |
| [config_page.h](src/config_page.h) | page SemX (HTML, CSS et JavaScript) en mémoire flash : `SEMX_HTML` |

Déroulement :

- **`setup()`** : chargement des réglages, branchement des messages WebSocket et MQTT, OTA, page `/`, démarrage d'ESPConnect, des sondes (`sensorsBegin()`), des relais (`relaysBegin()`) et de l'heure réseau.
- **`loop()`** : `espConnect.loop()` (WiFi, MQTT, messages reçus), `sensorsLoop()` (mesures), `relaysLoop()` (pompe, éclairage, état MQTT), `webLoop()` (mise à jour de la page).

Rien n'est bloquant : toutes les temporisations utilisent `millis()`.

### `lib/`

| Bibliothèque | Rôle |
|---|---|
| [ESPConnect](lib/ESPConnect/README.md) | WiFi avec portail de configuration, page `/status`, client MQTT (TCP, TLS, WebSocket), serveur web et WebSocket `/ws`, OTA, bouton de réinitialisation |
| [SensorDS18B20](lib/SensorDS18B20/README.md) | lecture non bloquante de plusieurs sondes DS18B20 sur un même bus |
| [SensorMoisture](lib/SensorMoisture/README.md) | lecture moyennée de la sonde d'humidité capacitive et conversion en pourcentage |
| [RelayController](lib/RelayController/README.md) | commande d'un relais (marche, arrêt, bascule, état) |

## Échanges WebSocket de la page SemX

Messages JSON sur `ws://<adresse-de-l-esp32>/ws`.

Page → ESP32 :

| Message | Effet |
|---|---|
| `{"cmd":"get"}` | demande l'état complet |
| `{"cmd":"save", "measure":s, "pumpOn":s, "pumpOff":s, "moistLow":%, "moistHigh":%, "lightStart":min, "lightOn":min, "dry":n, "wet":n}` | enregistre tous les réglages (vérifiés ensemble) |
| `{"cmd":"reset"}` | revient aux valeurs par défaut |
| `{"cmd":"name","id":"28FF…","name":"serre"}` | nomme une sonde (nom vide : sonde non publiée) |
| `{"cmd":"scan"}` | relance la détection des sondes |
| `{"cmd":"moisture"}` | lit la sonde d'humidité immédiatement |
| `{"cmd":"mode","relay":"pump"\|"light","mode":"auto"\|"moisture"\|"on"\|"off"}` | change le mode d'un relais |

ESP32 → page :

- `{"type":"state", …}` : heure, état et mode des relais, humidité, sondes et réglages enregistrés ;
- `{"type":"result","ok":true|false,"msg":"…"}` : réponse à une commande.

Les durées sont en secondes, sauf `lightStart` (minutes depuis minuit) et `lightOn` (minutes).
