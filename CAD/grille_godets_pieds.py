#!/usr/bin/env python3
"""Grille sur pieds pour le bac de semis de SemiX.

Grille mince tenue à mi-hauteur des godets par huit pieds posés sur le fond du bac.
Chaque godet passe dans une case qui l'empêche de basculer quand l'eau monte et que
le terreau sec le fait flotter. Elle ne l'empêche pas de se soulever : les godets sont
évasés, et un godet qui monte prend du jeu dans sa case. Il reste debout, puis
redescend quand le terreau a bu.

Le godet de mesure, en L autour du trop-plein, occupe la case d'angle (+x, +y) et y est
tenu comme les autres godets.

Les pieds sont des lames plates, imprimées à part et à plat, qui se placent dans
l'intervalle entre deux godets et s'emboîtent par un tenon dans une fente de la
grille. Imprimés d'un bloc avec la grille, des pieds de 31 mm ajouteraient 150 couches
presque vides, ralenties par le temps minimal de couche : près de 3 fois plus long.

Dépendances : pip install numpy scipy trimesh manifold3d shapely mapbox_earcut
Usage : python CAD/grille_godets_pieds.py

Repère du bac (STL/bac_semis_201x201x46_socle.stl) : z vers le haut, fond intérieur
à z = 2, parois intérieures à ±97, trop-plein à z = 27 dans le coin (+x, +y), arrivée
d'eau au fond en (-58.5, -58.5). Les STL sont exportés à plat, prêts à imprimer.
Unités : mm.
"""
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent.parent
STL_DIR = ROOT / "STL"
OUT = STL_DIR / "grille_godets_pieds_193x193x2.stl"

# Bac
FLOOR_Z = 2.0
INNER_HALF = 97.0
WATER_MAX_Z = 27.0        # haut du trop-plein

# Godets : pas des vues d'assemblage. Évasés : 28 mm au fond, 36 mm en haut.
PITCH = 39.0
N = 5

# Grille : au-dessus de l'eau, assez haut pour bien tenir le godet.
# À cette hauteur, un godet mesure 33,7 à 34,2 mm et il reste 4,8 mm entre deux godets.
GRID_Z = 33.0             # dessous de la grille
GRID_H = 2.4
RIB_T = 3.0               # laisse 0,9 à 1,2 mm de jeu de chaque côté du godet
WALL_CLEAR = 0.3          # bout des nervures contre la paroi

# Pieds : lames verticales dans l'intervalle entre deux godets, au milieu d'un côté de
# case. Elles évitent l'arrivée d'eau (-58.5, -58.5) et la case d'angle (+x, +y), où le
# godet de mesure en L entoure le trop-plein.
# (x, y, direction de la nervure au-dessus : "x" ou "y")
FEET = [(-39.0, -19.5, "x"), (39.0, -19.5, "x"), (-39.0, 19.5, "x"), (39.0, 19.5, "x"),
        (-58.5, 0.0, "y"), (58.5, 0.0, "y"), (0.0, -58.5, "x"), (0.0, 58.5, "x")]
FOOT_T = 1.8              # épaisseur de la lame, imprimée à plat
FOOT_W_BASE = 14.0        # largeur sur le fond
FOOT_W_TOP = 8.0          # largeur sous la grille
TENON_W = 6.0
TENON_H = GRID_H - 0.2    # ne dépasse pas du dessus de la grille
SLOT_CLEAR = 0.15         # jeu par côté entre le tenon et la fente
BOSS_W = 4.0              # nervure élargie autour de la fente : 0,4 mm de jeu avec les godets
BOSS_L = TENON_W + 2 * SLOT_CLEAR + 4.0
FOOT_OUT = STL_DIR / "grille_godets_pied_14x33.stl"

RIB_POS = (np.arange(N - 1) - (N - 2) / 2) * PITCH        # -58.5, -19.5, 19.5, 58.5


def box(x0, x1, y0, y1, z0, z1):
    m = trimesh.creation.box(extents=(x1 - x0, y1 - y0, z1 - z0))
    m.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return m


def foot_profile():
    """Lame dans son plan (u le long de la nervure, v vertical depuis le fond)."""
    h = GRID_Z - FLOOR_Z
    b, t, w = FOOT_W_BASE / 2, FOOT_W_TOP / 2, TENON_W / 2
    return [(-b, 0), (b, 0), (t, h), (w, h), (w, h + TENON_H), (-w, h + TENON_H), (-w, h), (-t, h)]


def make_foot():
    """Pied à plat, prêt à imprimer."""
    from shapely.geometry import Polygon
    m = trimesh.creation.extrude_polygon(Polygon(foot_profile()), FOOT_T)
    m.apply_translation(-m.bounds[0])
    return m


def placed_foot(x, y, direction):
    """Pied en place dans le bac."""
    m = make_foot()
    m.apply_translation((-m.extents[0] / 2, 0, -FOOT_T / 2))
    m.apply_transform([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])  # debout
    if direction == "y":
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (0, 0, 1)))
    return m.apply_translation((x, y, FLOOR_Z))


def make_grid():
    end = INNER_HALF - WALL_CLEAR
    t = RIB_T / 2
    parts = []
    for p in RIB_POS:
        parts.append(box(-end, end, p - t, p + t, GRID_Z, GRID_Z + GRID_H))
        parts.append(box(p - t, p + t, -end, end, GRID_Z, GRID_Z + GRID_H))
    slots = []
    sl, st = TENON_W / 2 + SLOT_CLEAR, FOOT_T / 2 + SLOT_CLEAR
    for x, y, d in FEET:
        boss = box(x - BOSS_L / 2, x + BOSS_L / 2, y - BOSS_W / 2, y + BOSS_W / 2,
                   GRID_Z, GRID_Z + GRID_H)
        slot = box(x - sl, x + sl, y - st, y + st, GRID_Z - 1, GRID_Z + GRID_H + 1)
        if d == "y":
            boss = box(x - BOSS_W / 2, x + BOSS_W / 2, y - BOSS_L / 2, y + BOSS_L / 2,
                       GRID_Z, GRID_Z + GRID_H)
            slot = box(x - st, x + st, y - sl, y + sl, GRID_Z - 1, GRID_Z + GRID_H + 1)
        parts.append(boss)
        slots.append(slot)
    grid = trimesh.boolean.union(parts, engine="manifold")
    return trimesh.boolean.difference([grid] + slots, engine="manifold")


def make_assembly():
    """Grille et pieds en place dans le bac."""
    return [make_grid()] + [placed_foot(*f) for f in FEET]


def main():
    assert GRID_Z > WATER_MAX_Z
    grid = make_grid()
    foot = make_foot()
    assert grid.is_volume and foot.is_volume
    flat = grid.copy()
    flat.apply_translation((0, 0, -flat.bounds[0, 2]))
    flat.export(OUT)
    foot.export(FOOT_OUT)
    for name, m in ((OUT.name, flat), (FOOT_OUT.name, foot)):
        e = m.extents
        print(f"{name} : {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm, {m.volume / 1000:.1f} cm3")


if __name__ == "__main__":
    main()
