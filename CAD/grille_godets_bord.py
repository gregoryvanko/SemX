#!/usr/bin/env python3
"""Grille de maintien des godets pour le bac de semis de SemiX.

Grille fine posée sur le bord du bac, qui cale les godets par le haut :
- des rebords passent au-dessus du bord des godets et les empêchent de se soulever
  quand le terreau sec flotte ;
- des lames de 2,5 mm, sous les nervures, descendent entre les godets pour les
  tenir droits ;
- des tronçons de jupe, sur les faces avant et arrière du bac, la tiennent en place
  par serrage. Les faces gauche et droite restent libres pour le support LED.
Dans le coin du trop-plein, la grille contourne le couvercle du godet de mesure et
le tient par deux de ses bords, sans gêner le capteur d'humidité ni la sonde.

Dépendances : pip install numpy scipy trimesh manifold3d shapely mapbox_earcut
Usage : python CAD/grille_godets_bord.py

Repère du bac (STL/bac_semis_201x201x46_socle.stl) : z vers le haut, fond intérieur
à z = 2, bord du bac à z = 46, parois intérieures à ±97 et extérieures à ±100,6.
Godets de 42 mm posés sur le fond : leur bord est à z = 44.
Le STL est exporté retourné, face du dessus sur le plateau. Unités : mm.
"""
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parent.parent
STL_DIR = ROOT / "STL"
OUT = STL_DIR / "grille_godets_haute_201x206x6.stl"

# Bac
INNER_HALF = 97.0
OUTER_HALF = 100.6
RIM_Z = 46.0
GODET_TOP_Z = 44.0        # 2 mm de fond + 42 mm de godet

# Godets : pas des vues d'assemblage, 3 mm entre les bords de deux godets
PITCH = 39.0
N = 5
GODET_TOP = 36.0
GODET_WALL = 1.2

# Grille
PLATE_T = 1.2             # épaisseur au-dessus du bord du bac
TOP_Z = RIM_Z + PLATE_T
CAP_W = 4.4               # rebord : recouvre 0,7 mm du bord de chaque godet
CAP_CLEAR = 0.4           # jeu vertical entre le rebord et le haut des godets
CAP_Z = GODET_TOP_Z + CAP_CLEAR
EDGE_W = INNER_HALF - (2 * PITCH + GODET_TOP / 2) + 0.7    # rebord le long des parois

# Lames sous les nervures, entre les godets. Le rebord empêche le godet de monter de
# plus de 0,4 mm : 2,5 mm de lame suffisent à le garder dans sa case. Plus courtes, elles
# réduisent le nombre de couches, ce qui compte le plus dans le temps d'impression.
FIN_T = 1.6               # dans un intervalle de 3 mm entre deux godets
FIN_DEPTH = 2.5           # sous le haut des godets
FIN_Z = GODET_TOP_Z - FIN_DEPTH
FIN_CHAMFER = 1.0         # biseau en bout de lame, pour entrer entre les godets
WALL_CLEAR = 0.3          # bout des nervures contre la paroi intérieure

# Tronçons de jupe sur les faces avant et arrière, serrés sur la paroi extérieure
SKIRT_T = 2.0
SKIRT_H = 4.5             # sous le bord du bac, pas plus bas que les lames
SKIRT_L = 24.0
SKIRT_X = (-70.0, 0.0, 70.0)
SKIRT_FIT = 0.2           # jeu entre la jupe et la paroi
CRUSH = 0.35              # nervure d'écrasement au milieu de chaque tronçon : serrage 0,15 mm
CRUSH_W = 3.0

# Godet de mesure et son couvercle (STL/couvercle_godet_mesure_36x19.stl), dans le coin
# du trop-plein. Le couvercle, emboîté sur le godet, a son dessus à 2 mm au-dessus du
# bord du godet, ses bords à x -22,6 (languette) / +19,7 et y ±10,9 du centre du godet,
# et sa jupe descend de 6 mm.
MESURE_XY = (78.0, 69.5)
LID_X = (-19.7, 19.7)
LID_Y = (-10.9, 10.9)
TAB_X = -22.6             # languette côté centre du bac
TAB_Y = (-5.0, 5.0)
LID_TOP_Z = GODET_TOP_Z + 2.0
LID_CLEAR = 0.6           # jeu autour du couvercle
# Avec le godet centré en x = 78, la jupe du couvercle (19,7 mm) dépasserait la paroi
# (97) : le godet est forcément un peu décalé vers le centre. On laisse libre jusqu'à
# 1,5 mm de décalage.
LID_SHIFT = 1.5
LID_HOLD_Z = LID_TOP_Z + 0.3   # dessous de la grille au-dessus du couvercle : 0,9 mm d'épaisseur

RIB_POS = (np.arange(N - 1) - (N - 2) / 2) * PITCH        # -58.5, -19.5, 19.5, 58.5


def box(x0, x1, y0, y1, z0, z1):
    m = trimesh.creation.box(extents=(x1 - x0, y1 - y0, z1 - z0))
    m.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return m


def prism_x(points_yz, x0, x1):
    """Profil (y, z) extrudé selon x, de x0 à x1."""
    m = trimesh.creation.extrude_polygon(Polygon(points_yz), x1 - x0)
    m.apply_transform([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
    return m


def rotz(m, quarter_turns):
    r = trimesh.transformations.rotation_matrix(quarter_turns * np.pi / 2, (0, 0, 1))
    return m.copy().apply_transform(r)


def union(meshes):
    return trimesh.boolean.union(meshes, engine="manifold")


def fin(y, x0, x1):
    """Lame selon x, centrée en y, biseautée en dessous."""
    f = FIN_T / 2
    return prism_x([(y - f, CAP_Z + 0.01), (y + f, CAP_Z + 0.01), (y + f, FIN_Z + FIN_CHAMFER),
                    (y, FIN_Z), (y - f, FIN_Z + FIN_CHAMFER)], x0, x1)


def lid_reliefs():
    """Volumes laissés libres autour du couvercle du godet de mesure."""
    cx, cy = MESURE_XY
    c = LID_CLEAR
    cap_edge = RIB_POS[-1] - CAP_W / 2         # pas de lamelle fine le long de la nervure
    body = box(max(cx + LID_X[0] - c - LID_SHIFT, cap_edge), INNER_HALF + 2.0, cy + LID_Y[0] - c, cy + LID_Y[1] + c,
               0, LID_HOLD_Z)
    tab = box(cx + TAB_X - c - LID_SHIFT, cx + LID_X[0], cy + TAB_Y[0] - c, cy + TAB_Y[1] + c, 0, LID_HOLD_Z)
    # Ouverture pour le capteur et la sonde : tout le dessus du couvercle, sauf ses
    # deux bords tenus par les nervures qui passent au-dessus.
    hold = CAP_W / 2 + RIB_POS[-1]
    window = box(hold + 0.5, INNER_HALF - 1.0, hold + 0.5, cy + LID_Y[1] - 1.5, 0, TOP_Z + 1)
    return [body, tab, window]


def make_grid():
    end = INNER_HALF - WALL_CLEAR
    parts = []

    # Nervures en T : rebord au-dessus des godets et lame entre eux
    for p in RIB_POS:
        rib = box(-end, end, p - CAP_W / 2, p + CAP_W / 2, CAP_Z, TOP_Z)
        parts += [rib, rotz(rib, 1), fin(p, -end, end), rotz(fin(p, -end, end), 1)]

    # Cadre posé sur le bord du bac, et rebord au-dessus des godets le long des parois
    ring = [box(-OUTER_HALF, OUTER_HALF, INNER_HALF, OUTER_HALF, RIM_Z, TOP_Z),
            box(-end, end, INNER_HALF - EDGE_W, INNER_HALF, CAP_Z, TOP_Z)]
    for k in range(4):
        parts += [rotz(m, k) for m in ring]

    # Tronçons de jupe avant et arrière, avec une nervure d'écrasement verticale
    y_in = OUTER_HALF + SKIRT_FIT
    z0 = RIM_Z - SKIRT_H
    for x in SKIRT_X:
        skirt = box(x - SKIRT_L / 2, x + SKIRT_L / 2, y_in, y_in + SKIRT_T, z0, TOP_Z)
        tie = box(x - SKIRT_L / 2, x + SKIRT_L / 2, INNER_HALF, y_in + SKIRT_T, RIM_Z, TOP_Z)
        bump = box(x - CRUSH_W / 2, x + CRUSH_W / 2, y_in - CRUSH, y_in + 0.01, z0, RIM_Z)
        for m in (skirt, tie, bump):
            parts += [m, rotz(m, 2)]

    grid = union(parts)
    return trimesh.boolean.difference([grid, union(lid_reliefs())], engine="manifold")


def main():
    grid = make_grid()
    assert grid.is_volume
    printed = grid.copy()
    printed.apply_transform(np.diag([1, -1, -1, 1]))        # retournée, dessus sur le plateau
    printed.apply_translation((0, 0, -printed.bounds[0, 2]))
    printed.export(OUT)
    ext = grid.extents
    print(f"{OUT.name} : {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm, "
          f"{grid.volume / 1000:.1f} cm3, ~{grid.volume / 1000 * 1.27:.0f} g en PETG")
    print(f"Ouverture des cases : {PITCH - CAP_W:.1f} mm, recouvrement des godets : "
          f"{(CAP_W - (PITCH - GODET_TOP)) / 2:.1f} mm")
    return grid


if __name__ == "__main__":
    main()
