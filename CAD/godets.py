#!/usr/bin/env python3
"""Godets de SemiX : godet de semis et godet de mesure.

Les godets boivent par le dessous quand l'eau monte dans le bac. Avec seulement 9 trous
de 3 mm au fond (64 mm² d'ouverture), l'eau entrait trop lentement et le terreau sec,
peu mouillable, restait sec au-dessus. Cette version garde les mêmes dimensions et
ouvre davantage le godet, sans laisser fuir le terreau :

- fond : 13 trous de 4 mm au lieu de 9 de 3 mm, soit 2,5 fois plus d'ouverture ;
- parois : 3 fentes verticales de 1,5 mm sur chaque face, du fond jusqu'à 20 mm, sous
  le niveau du trop-plein. L'eau mouille le terreau par les côtés dès qu'elle monte, au
  lieu de ne l'atteindre que par le fond, et l'air chassé du terreau s'échappe aussi
  par les fentes.

Dépendances : pip install numpy trimesh manifold3d
Usage : python CAD/godets.py

Repère : z vers le haut, dessous des pieds à z = 0, godet centré en x et y. Dans le bac,
le godet repose sur le fond (z = 2 du bac) et le haut du trop-plein (z = 27 du bac) est
à z = 25 du godet. Les STL sont exportés à l'endroit, prêts à imprimer. Unités : mm.
"""
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent.parent
STL_DIR = ROOT / "STL"

# Corps, identique à la version précédente
H = 42.0                  # hauteur totale
FOOT_H = 4.0              # pieds sous le fond
FLOOR_T = 1.2             # épaisseur du fond
WALL_T = 0.8              # épaisseur des parois, mesurée à l'horizontale
HALF_BOTTOM = 14.0        # demi-côté extérieur sous le fond (28 mm)
HALF_TOP = 18.0           # demi-côté extérieur en haut (36 mm)
FOOT_IN = 8.0             # pieds de 6 × 6 mm dans les coins, de 8 à 14 mm de l'axe
MESURE_HALF_Y = 9.5       # godet de mesure : 19 mm, parois droites suivant y

WATER_MAX_Z = 25.0        # haut du trop-plein, dans le repère du godet

# Trous du fond
HOLE_D = 4.0
HOLE_PITCH = 6.0          # grille 3 × 3 ; les trous d'angle ne touchent pas les pieds
EDGE_HOLE = 10.5          # trous supplémentaires au milieu des côtés, hors des pieds

# Fentes des parois
SLOT_W = 1.5              # retient le terreau, laisse passer l'eau
SLOT_TOP = 20.0           # haut des fentes, sous WATER_MAX_Z
SLOT_PITCH = 7.0          # 3 fentes par face ; 1 seule sur les petites faces du godet de mesure

FLOOR_Z = FOOT_H + FLOOR_T


def half_at(z, h0=HALF_BOTTOM, h1=HALF_TOP):
    return h0 + (h1 - h0) * (z - FOOT_H) / (H - FOOT_H)


def frustum(hx0, hx1, hy0, hy1, z0, z1):
    """Tronc de pyramide à base rectangulaire, de (hx0, hy0) en z0 à (hx1, hy1) en z1."""
    v = [(-hx0, -hy0, z0), (hx0, -hy0, z0), (hx0, hy0, z0), (-hx0, hy0, z0),
         (-hx1, -hy1, z1), (hx1, -hy1, z1), (hx1, hy1, z1), (-hx1, hy1, z1)]
    return trimesh.convex.convex_hull(np.array(v))


def box(x0, x1, y0, y1, z0, z1):
    m = trimesh.creation.box(extents=(x1 - x0, y1 - y0, z1 - z0))
    m.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return m


def hole(x, y):
    c = trimesh.creation.cylinder(radius=HOLE_D / 2, height=FLOOR_T + 2, sections=32)
    return c.apply_translation((x, y, FOOT_H + FLOOR_T / 2))


def slot(axis, side, u, n_in, n_out):
    """Fente traversant la paroi normale à `axis`, du côté `side` (±1), centrée en `u`.
    La boîte va de n_in (dans le vide du godet) à n_out (dehors), du fond à SLOT_TOP."""
    n0, n1 = sorted((side * n_in, side * n_out))
    if axis == "x":
        return box(n0, n1, u - SLOT_W / 2, u + SLOT_W / 2, FLOOR_Z, SLOT_TOP)
    return box(u - SLOT_W / 2, u + SLOT_W / 2, n0, n1, FLOOR_Z, SLOT_TOP)


def make_godet(half_y=None):
    """Godet de semis (half_y=None) ou godet de mesure (half_y : demi-largeur, parois
    droites suivant y)."""
    mesure = half_y is not None
    hy0 = half_y if mesure else HALF_BOTTOM
    hy1 = half_y if mesure else HALF_TOP
    outer = frustum(HALF_BOTTOM, HALF_TOP, hy0, hy1, FOOT_H, H)
    z0, z1 = FLOOR_Z, H + 1
    ix0, ix1 = half_at(z0) - WALL_T, half_at(z1) - WALL_T
    iy0, iy1 = (half_y - WALL_T,) * 2 if mesure else (ix0, ix1)
    inner = frustum(ix0, ix1, iy0, iy1, z0, z1)

    # Pieds de 6 mm dans les coins, au ras des bords extérieurs
    fy = hy0 - (HALF_BOTTOM - FOOT_IN)
    feet = [box(min(sx * FOOT_IN, sx * HALF_BOTTOM), max(sx * FOOT_IN, sx * HALF_BOTTOM),
                min(sy * fy, sy * hy0), max(sy * fy, sy * hy0), 0, FOOT_H)
            for sx in (1, -1) for sy in (1, -1)]
    body = trimesh.boolean.union([outer] + feet, engine="manifold")

    g = (-HOLE_PITCH, 0.0, HOLE_PITCH)
    holes = [hole(x, y) for x in g for y in g] + [hole(s * EDGE_HOLE, 0) for s in (1, -1)]
    if not mesure:
        holes += [hole(0, s * EDGE_HOLE) for s in (1, -1)]

    three = (-SLOT_PITCH, 0.0, SLOT_PITCH)
    x_in = ix0 - 2.0                  # dans le vide du godet, sous la paroi évasée
    cuts = []
    for s in (1, -1):
        for u in ((0.0,) if mesure else three):          # faces ±x
            cuts.append(slot("x", s, u, x_in, HALF_TOP + 1))
        y_in = (half_y - WALL_T - 1.0) if mesure else x_in
        y_out = (half_y + 1.0) if mesure else HALF_TOP + 1
        for u in three:                                    # faces ±y
            cuts.append(slot("y", s, u, y_in, y_out))
    m = trimesh.boolean.difference([body, inner] + holes + cuts, engine="manifold")
    return m, len(holes), len(cuts)


def main():
    assert SLOT_TOP < WATER_MAX_Z
    # Fentes à l'écart des arêtes : la fente extérieure doit rester dans la face la plus étroite.
    assert SLOT_PITCH + SLOT_W / 2 < half_at(FLOOR_Z) - WALL_T - 3.0
    # Trous d'angle hors des pieds (diagonale)
    assert np.hypot(FOOT_IN - HOLE_PITCH, FOOT_IN - HOLE_PITCH) > HOLE_D / 2

    for name, (m, n_holes, n_slots) in (("godet_semis_36x36x42.stl", make_godet()),
                                        ("godet_mesure_36x19x42.stl", make_godet(MESURE_HALF_Y))):
        assert m.is_volume and m.body_count == 1, name
        m.export(STL_DIR / name)
        e = m.extents
        area = n_holes * np.pi * HOLE_D ** 2 / 4
        print(f"{name} : {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm, {m.volume / 1000:.2f} cm3, "
              f"{n_holes} trous ({area:.0f} mm²), {n_slots} fentes")


if __name__ == "__main__":
    main()
