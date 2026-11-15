# SemX

SemX est une chambre de culture automatisée pour la germination et les premières semaines des semis. Un ESP32 mesure la température et l'humidité du substrat, puis pilote l'arrosage et l'éclairage. Le tout se règle depuis une page web et peut s'intégrer à une domotique par MQTT.

## Principe

- **Arrosage par capillarité** : un bac de semis est posé sur un réservoir d'eau. Une pompe immergée remplit le bac, les godets absorbent l'eau par leur fond, et un trop-plein renvoie l'excédent dans le réservoir.
- **Mesures** : deux sondes DS18B20 mesurent la température de l'eau du réservoir et celle du semis. Un capteur capacitif mesure l'humidité du substrat dans un godet de mesure.
- **Pilotage** : un relais commande la pompe (cycle temporisé ou selon l'humidité du sol), un autre allume et éteint les panneaux LED à heure fixe.
- **Supervision** : la page web SemX permet de tout régler, et les mesures ainsi que l'état des relais sont publiés sur MQTT.

## Organisation du dépôt

| Dossier | Contenu | Documentation |
|---|---|---|
| [`V1/`](V1/) | Première version de la partie mécanique : fichiers STL à imprimer (réservoir, bac, godets, grille, support LED, boîtier) et scripts Python qui les génèrent (`CAD/`) | [V1/README.md](V1/README.md) |
| [`PlatformIO/`](PlatformIO/) | Firmware de l'ESP32 : mesures, pompe, éclairage, page web, MQTT, OTA | [PlatformIO/README.md](PlatformIO/README.md) |
| [`PCB/`](PCB/) | Circuit imprimé simple face à graver à la CNC : script de génération, Gerber et G-code | [PCB/README.md](PCB/README.md) |

## Matériel et mécanique — [V1/README.md](V1/README.md)

Ce document décrit la version 1 du matériel :

- les [objectifs](V1/README.md#objectifs) de la chambre de culture et les [éléments techniques](V1/README.md#éléments-techniques) (ESP32, capteurs, actionneurs) ;
- le [brochage](V1/README.md#brochage) des capteurs et des relais ;
- le [réservoir, le bac et les godets](V1/README.md#réservoir-bac-et-godets), dont le godet de mesure et la grille sur pieds ;
- le [support des panneaux LED](V1/README.md#support-des-panneaux-led), réglable en hauteur ;
- le [boîtier de l'électronique](V1/README.md#boîtier-de-lélectronique).

## Circuit imprimé — [PCB/README.md](PCB/README.md)

Ce document décrit la carte qui reçoit l'ESP32 :

- l'[implantation](PCB/README.md#implantation) des composants, leurs raccordements et leurs perçages ;
- l'[usinage](PCB/README.md#usinage) à la CNC et le [montage](PCB/README.md#montage) ;
- la [régénération](PCB/README.md#régénérer-les-fichiers) des fichiers Gerber, du G-code et des images par le script `pcb_semx.py`.

## Firmware — [PlatformIO/README.md](PlatformIO/README.md)

Ce document décrit le logiciel de l'ESP32 :

- la [compilation et le téléversement](PlatformIO/README.md#compilation-et-téléversement), par USB ou par le réseau (OTA) ;
- le [premier démarrage et la connexion WiFi](PlatformIO/README.md#premier-démarrage-et-connexion-wifi) ;
- le [fonctionnement](PlatformIO/README.md#fonctionnement) des mesures, de la pompe et de l'éclairage ;
- la [page SemX](PlatformIO/README.md#page-semx) et les [topics MQTT](PlatformIO/README.md#mqtt) ;
- les [réglages](PlatformIO/README.md#réglages-et-mémoire) et l'[organisation du code](PlatformIO/README.md#organisation-du-code).

## Pour démarrer

1. Imprimer les pièces de [`V1/STL/`](V1/STL/) et assembler le bac, le réservoir et le support LED (voir [V1/README.md](V1/README.md)).
2. Graver et monter le [circuit imprimé](PCB/README.md), ou câbler l'ESP32 suivant le [brochage](V1/README.md#brochage).
3. Téléverser le firmware avec PlatformIO, puis configurer le WiFi par le point d'accès **SemX-Setup** (voir [PlatformIO/README.md](PlatformIO/README.md)).
4. Régler la pompe, l'éclairage et la calibration de l'humidité sur la page web SemX.
