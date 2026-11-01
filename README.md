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

## Support des panneaux LED

Support imprimable pour 4 panneaux LED de 80 × 300 mm, réglable en hauteur par crans de 15 mm. Deux pieds sont collés sur les faces gauche et droite du réservoir et portent chacun deux colonnes, espacées de la largeur de deux panneaux. Une traverse relie les deux colonnes de chaque face, ce qui empêche le support de se tordre. Les panneaux, orientés selon l'axe gauche-droite, passent à deux entre les colonnes et un de chaque côté, et les faces avant et arrière restent libres pour accéder aux semis ou sortir le bac.

![Support LED monté sur le réservoir et le bac de semis](CAD/images/support_led_vue.png)

| Pièce (`STL/`) | Quantité | Masse unitaire | Impression |
|---|---|---|---|
| `support_led_pied.stl` | 2 | 73 g | Telle quelle, avec bordure (brim) |
| `support_led_colonne.stl` | 4 | 29 g | Telle quelle, en diagonale du plateau, remplissage 10 % |
| `support_led_traverse.stl` | 2 | 39 g | Telle quelle, en diagonale du plateau |
| `support_led_goupille.stl` | 4 + rechange | 0,7 g | À plat |

![Les quatre pièces à imprimer, à des échelles différentes](CAD/images/support_led_pieces.png)

Les fichiers sont déjà positionnés sur le plateau de 256 mm : ne pas utiliser l'arrangement automatique pour la colonne et la traverse. Toutes les pièces s'impriment sans support. La bordure ne concerne que le pied, haut et étroit : la colonne et la traverse laissent trop peu de marge sur le plateau pour en recevoir une. Le tranchage dans Bambu Studio (X1 Carbon, buse 0,4, PETG HF, couche 0,20 mm, 3 parois, remplissage 20 %, 10 % pour les colonnes) donne environ 345 g de filament et 8 h 40 d'impression. Le PETG est préférable au PLA pour sa tenue à l'humidité et à la chaleur des panneaux.

### Montage

![Vue éclatée du support](CAD/images/support_led_eclate.png)

1. Vider et sécher le réservoir, puis poncer légèrement et dégraisser la paroi et le dos des pieds.
2. Coller un pied sur chaque face gauche et droite à la colle époxy bicomposant : pied posé sur la table et centré sur la face, avec le même débord de 2 mm à chaque coin. Respecter le temps de durcissement complet. Le bac reste amovible : le dos du pied s'arrête sous le joint avec le réservoir, et les fûts passent à 0,4 mm de sa paroi.
3. Insérer les colonnes dans les fûts, la longue partie sans trous vers le bas. Elles tiennent par emboîtement, sans goupille.
4. Enfiler une traverse sur les deux colonnes de chaque face, la paroi continue vers l'extérieur, et la bloquer avec une goupille par colonne, insérée côté bac.
5. Poser les panneaux dans les poches, LED vers le bas : deux entre les colonnes et un de chaque côté. Les câbles passent au-dessus de la paroi de 10 mm des traverses.

Pour déplacer le réservoir, sortir les colonnes en les soulevant. Les pieds restent collés.

| Pied collé sur le réservoir | Coulisseau et goupille, panneaux avant retirés |
|---|---|
| ![Pied collé sur la face du réservoir](CAD/images/support_led_detail_pied.png) | ![Traverse, coulisseau et goupille](CAD/images/support_led_detail_traverse.png) |

### Réglage de la hauteur

![Support aux hauteurs minimale et maximale](CAD/images/support_led_hauteurs.png)

Chaque colonne a 6 trous espacés de 30 mm et chaque coulisseau en a deux, décalés de 15 mm : selon le trou utilisé, la traverse se déplace par crans de 15 mm. Monter un côté puis l'autre, un cran à la fois, en maintenant les colonnes pour qu'elles ne remontent pas avec la traverse.

- La face LED se règle sur 12 positions, de 198 à 363 mm au-dessus de la table, soit de **68 à 233 mm au-dessus du haut des godets**.
- Le cran le plus bas passe 6 mm au-dessus du capteur d'humidité, qui reste le point le plus haut du bac.

### Limites

- Les deux panneaux centraux se touchent presque et couvrent le bac jusqu'à 18 mm de ses bords avant et arrière. Les deux panneaux extérieurs sont entièrement en dehors de l'emprise du bac et n'éclairent les semis qu'en biais.
- La paroi des traverses dépasse de 7 mm au-dessus de l'appui des panneaux : un câble qui sort du petit côté d'un panneau mince doit remonter pour la franchir.
- La traverse tient en un seul morceau sur le plateau, au prix d'une longueur de 316 mm : elle porte les panneaux extérieurs sur 55 des 80 mm de leur largeur, et les retient uniquement côté intérieur.

Encombrement : 307 × 367 × 392 mm. Les poches sont ouvertes par le haut et fonctionnent quelle que soit l'épaisseur des panneaux. Le script paramétrique [`CAD/support_led.py`](CAD/support_led.py) permet d'ajuster les dimensions : `POCKET_W` pour la largeur des poches, `COL` pour la section des colonnes, `FIT` pour le jeu des coulisseaux, `BAR_L` pour la longueur des colonnes. Le script [`CAD/rendu_support_led.py`](CAD/rendu_support_led.py) régénère les images de cette section.

## Licence

Le projet est distribué sous licence Apache 2.0. Consulter le fichier [LICENSE](LICENSE) pour en connaître les conditions.
