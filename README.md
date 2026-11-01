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

Support imprimable pour 4 panneaux LED de 80 × 300 mm, réglable en hauteur par crans de 15 mm. Deux pieds sont collés sur les faces gauche et droite du réservoir et portent chacun deux colonnes, espacées de la largeur de deux panneaux. Une traverse relie les deux colonnes de chaque face, ce qui empêche le support de se tordre. Les panneaux, épais de 1 mm, sont collés sous les traverses par leur face arrière, avec huit morceaux d'adhésif double face 3M de 30 × 50 mm. Deux entretoises relient les traverses par-dessus les panneaux. Les panneaux, orientés selon l'axe gauche-droite, passent à deux entre les colonnes et un de chaque côté, et les faces avant et arrière restent libres pour accéder aux semis ou sortir le bac.

![Support LED monté sur le réservoir et le bac de semis](CAD/images/support_led_vue.png)

| Pièce (`STL/`) | Quantité | Masse unitaire | Impression |
|---|---|---|---|
| `support_led_pied.stl` | 2 | 72 g | Telle quelle, avec bordure (brim) |
| `support_led_colonne.stl` | 4 | 29 g | Telle quelle, en diagonale du plateau, remplissage 10 % |
| `support_led_traverse.stl` | 2 | 51 g | Telle quelle, en diagonale du plateau, bande de collage sur le plateau |
| `support_led_entretoise.stl` | 2 | 15 g | Telle quelle, corps sur le plateau, pattes vers le haut |
| `support_led_goupille.stl` | 4 + rechange | 0,8 g | À plat |

![Les pièces à imprimer, à des échelles différentes](CAD/images/support_led_pieces.png)

Les fichiers sont déjà positionnés sur le plateau de 256 mm : ne pas utiliser l'arrangement automatique pour la colonne et la traverse. Toutes les pièces s'impriment sans support. La bordure ne concerne que le pied, haut et étroit : la colonne et la traverse laissent trop peu de marge sur le plateau pour en recevoir une. Le tranchage dans Bambu Studio (X1 Carbon, buse 0,4, PETG HF, couche 0,20 mm, 3 parois, remplissage 20 %, 10 % pour les colonnes) donne environ 395 g de filament et 10 h 20 d'impression. Le PETG est préférable au PLA pour sa tenue à l'humidité et à la chaleur des panneaux.

### Montage

![Vue éclatée du support](CAD/images/support_led_eclate.png)

1. Vider et sécher le réservoir, puis poncer légèrement et dégraisser la paroi et le dos des pieds.
2. Coller un pied sur chaque face gauche et droite à la colle époxy bicomposant : pied posé sur la table et centré sur la face, avec le même retrait de 0,3 mm à chaque coin : le pied est un peu moins large que le réservoir. Respecter le temps de durcissement complet. Le bac reste amovible : le dos du pied s'arrête sous le joint avec le réservoir, et les fûts passent à 0,4 mm de sa paroi.
3. Enfoncer les colonnes dans les fûts, la longue partie sans trous vers le bas et la face sans nervure tournée au choix. Leurs nervures d'écrasement suppriment le jeu : elles tiennent en force, sans goupille.
4. Enfiler une traverse sur les deux colonnes de chaque face, la paroi vers l'extérieur, au même cran des deux côtés. Glisser une entretoise entre les coulisseaux en vis-à-vis, à l'avant et à l'arrière, puis bloquer chaque coulisseau avec une goupille, insérée côté bac à travers la patte de l'entretoise.
5. Dégraisser la bande de collage et l'arrière des panneaux à l'alcool isopropylique, puis poser les adhésifs sous la bande, le long de la paroi, chacun dans l'axe d'une nervure.
6. Présenter chaque panneau sous les traverses, LED vers le bas, le bout à 1 mm du bord extérieur de la bande : deux entre les colonnes et un de chaque côté. Presser fermement chaque collage. Le côté de 50 mm de l'adhésif suit la largeur du panneau.
7. Brancher les fiches USB-C sous les panneaux : rien ne les gêne, la traverse restant au-dessus.

Pour déplacer le réservoir, sortir les colonnes en tirant fermement vers le haut. Les pieds restent collés.

| Pied collé sur le réservoir | Coulisseau et goupille, panneaux avant retirés |
|---|---|
| ![Pied collé sur la face du réservoir](CAD/images/support_led_detail_pied.png) | ![Traverse, coulisseau et goupille](CAD/images/support_led_detail_traverse.png) |

![Adhésifs sous la bande de collage, vus de dessous](CAD/images/support_led_detail_collage.png)

### Réglage de la hauteur

![Support aux hauteurs minimale et maximale](CAD/images/support_led_hauteurs.png)

Chaque colonne a 6 trous espacés de 30 mm et chaque coulisseau en a deux, décalés de 15 mm : selon le trou utilisé, le cadre se déplace par crans de 15 mm. Une fois collés, les panneaux et les traverses forment un seul cadre : retirer les quatre goupilles, soulever le cadre d'un bloc par ses entretoises en le gardant horizontal, puis remettre les goupilles. Ne pas monter un côté avant l'autre, ce qui tordrait les panneaux et décollerait les adhésifs.

- La face LED se règle sur 12 positions, de 196 à 361 mm au-dessus de la table, soit de **66 à 231 mm au-dessus du haut des godets**, pour un adhésif de 1 mm.
- Le cran le plus bas passe 4 mm au-dessus du capteur d'humidité, qui reste le point le plus haut du bac.

### Limites

- Les deux panneaux centraux se touchent presque et couvrent le bac jusqu'à 20 mm de ses bords avant et arrière. Les deux panneaux extérieurs sont presque entièrement en dehors de l'emprise du bac et n'éclairent les semis qu'en biais.
- Sur les panneaux extérieurs, l'adhésif est décalé de 7 mm vers l'intérieur, car la traverse s'arrête à 316 mm pour tenir sur le plateau.
- Les panneaux ne sont tenus qu'à leurs deux bouts, sur 240 mm de portée libre. Selon leur matière, ils peuvent fléchir de quelques millimètres en leur milieu.
- La tenue de l'adhésif dépend de la chaleur des panneaux et de la surface imprimée, et reste à vérifier.

Encombrement : 302 × 357 × 397 mm, et le pied ne dépasse pas la largeur du réservoir. Le script paramétrique [`CAD/support_led.py`](CAD/support_led.py) permet d'ajuster les dimensions : `TAPE_L` et `TAPE_W` pour l'adhésif, `COL` pour la section des colonnes, `FIT` pour le jeu des coulisseaux, `CRUSH` pour le serrage des nervures, `BAR_L` pour la longueur des colonnes. Le script [`CAD/rendu_support_led.py`](CAD/rendu_support_led.py) régénère les images de cette section.

## Licence

Le projet est distribué sous licence Apache 2.0. Consulter le fichier [LICENSE](LICENSE) pour en connaître les conditions.
