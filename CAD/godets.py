#!/usr/bin/env python3
"""Godets de SemiX : godet de semis et godet de mesure en L.

Les godets boivent par le dessous quand l'eau monte dans le bac. Avec seulement 9 trous
de 3 mm au fond (64 mm² d'ouverture), l'eau entrait trop lentement et le terreau sec,
peu mouillable, restait sec au-dessus. Cette version garde les mêmes dimensions et
ouvre davantage le godet, sans laisser fuir le terreau :

- fond : 13 trous de 4 mm au lieu de 9 de 3 mm, soit 2,5 fois plus d'ouverture ;
- parois : 3 fentes verticales de 1,5 mm sur chaque face, du fond jusqu'à 20 mm, sous
  le niveau du trop-plein. L'eau mouille le terreau par les côtés dès qu'elle monte, au
  lieu de ne l'atteindre que par le fond, et l'air chassé du terreau s'échappe aussi
  par les fentes.

Le godet de mesure occupe la case d'angle du bac, celle du trop-plein. Il a l'emprise et
l'évasement d'un godet de semis, mais son coin est échancré en L sur toute la hauteur
autour du tube du trop-plein. Il tient donc dans la grille comme les autres godets, sans
support. Le capteur d'humidité se plante dans une branche du L, la sonde DS18B20 dans
l'autre, directement dans le terreau.

Dépendances : pip install numpy trimesh manifold3d
Usage : python CAD/godets.py

Repère : z vers le haut, dessous des pieds à z = 0, godet centré en x et y. Dans le bac,
le godet repose sur le fond (z = 2 du bac) et le haut du trop-plein (z = 27 du bac) est
à z = 25 du godet. Le godet de mesure est centré sur la case d'angle (78, 78) du bac,
échancrure vers le coin (+x, +y), où se trouve le trop-plein. Les STL sont exportés à l'endroit, prêts à imprimer. Unités : mm.
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

# Godet de mesure en L. Le trop-plein du bac, tube de Ø 14 mm centré en (89, 89), est
# en (11, 11) dans le repère du godet : il occupe de 4 à 18 mm de l'axe.
OVERFLOW_XY = 11.0
OVERFLOW_R = 7.0
NOTCH = 3.0               # échancrure : x > 3 et y > 3, à 1 mm du tube

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


def corner_feet(skip=()):
    """Pieds de 6 mm dans les coins, au ras des bords extérieurs."""
    return [box(min(sx * FOOT_IN, sx * HALF_BOTTOM), max(sx * FOOT_IN, sx * HALF_BOTTOM),
                min(sy * FOOT_IN, sy * HALF_BOTTOM), max(sy * FOOT_IN, sy * HALF_BOTTOM), 0, FOOT_H)
            for sx in (1, -1) for sy in (1, -1) if (sx, sy) not in skip]


def shell():
    """Corps évasé plein et son vide intérieur."""
    outer = frustum(HALF_BOTTOM, HALF_TOP, HALF_BOTTOM, HALF_TOP, FOOT_H, H)
    z0, z1 = FLOOR_Z, H + 1
    i0, i1 = half_at(z0) - WALL_T, half_at(z1) - WALL_T
    return outer, frustum(i0, i1, i0, i1, z0, z1)


def make_godet():
    """Godet de semis."""
    outer, inner = shell()
    body = trimesh.boolean.union([outer] + corner_feet(), engine="manifold")
    g = (-HOLE_PITCH, 0.0, HOLE_PITCH)
    holes = [hole(x, y) for x in g for y in g]
    holes += [hole(s * EDGE_HOLE, 0) for s in (1, -1)] + [hole(0, s * EDGE_HOLE) for s in (1, -1)]
    x_in = half_at(FLOOR_Z) - WALL_T - 2.0     # dans le vide du godet, sous la paroi évasée
    cuts = [slot(axis, s, u, x_in, HALF_TOP + 1)
            for axis in "xy" for s in (1, -1) for u in (-SLOT_PITCH, 0.0, SLOT_PITCH)]
    m = trimesh.boolean.difference([body, inner] + holes + cuts, engine="manifold")
    return m, len(holes), len(cuts)


MESURE_HOLES = [(-HOLE_PITCH, -HOLE_PITCH), (0.0, -HOLE_PITCH), (HOLE_PITCH, -HOLE_PITCH),
                (-HOLE_PITCH, 0.0), (0.0, 0.0), (-HOLE_PITCH, HOLE_PITCH),
                (-EDGE_HOLE, 0.0), (0.0, -EDGE_HOLE)]


def mesure_feet():
    """3 pieds d'angle, et un pied au bout de chaque branche, contre l'échancrure."""
    return corner_feet(skip=((1, 1),)) + [
        box(FOOT_IN, HALF_BOTTOM, NOTCH - 6.0, NOTCH, 0, FOOT_H),
        box(NOTCH - 6.0, NOTCH, FOOT_IN, HALF_BOTTOM, 0, FOOT_H)]


def make_godet_mesure():
    """Godet de mesure en L : godet de semis dont le coin (+x, +y) est échancré sur toute
    la hauteur autour du trop-plein."""
    outer, inner = shell()
    notch = box(NOTCH, HALF_TOP + 1, NOTCH, HALF_TOP + 1, -1, H + 2)
    wall = box(NOTCH - WALL_T, HALF_TOP + 1, NOTCH - WALL_T, HALF_TOP + 1, -1, H + 2)
    body = trimesh.boolean.union([outer] + mesure_feet(), engine="manifold")
    body = trimesh.boolean.difference([body, notch], engine="manifold")
    cavity = trimesh.boolean.difference([inner, wall], engine="manifold")

    holes = [hole(x, y) for x, y in MESURE_HOLES]

    a = half_at(FLOOR_Z) - WALL_T          # intérieur au niveau du fond, faces évasées
    b = NOTCH - WALL_T                     # intérieur, faces de l'échancrure
    x_in = a - 2.0
    cuts = []
    for axis in "xy":
        # Grande face (-x ou -y) : 3 fentes
        cuts += [slot(axis, -1, u, x_in, HALF_TOP + 1) for u in (-SLOT_PITCH, 0.0, SLOT_PITCH)]
        # Bout de branche (+x ou +y) : 2 fentes, de -a à b
        c = (b - a) / 2
        cuts += [slot(axis, 1, c + d, x_in, HALF_TOP + 1) for d in (-3.5, 3.5)]
        # Face de l'échancrure : 1 fente, de b à a
        cuts.append(slot(axis, 1, (a + b) / 2, b - 1.0, NOTCH + 1.0))
    m = trimesh.boolean.difference([body, cavity] + holes + cuts, engine="manifold")
    return m, len(holes), len(cuts)


def check_mesure():
    a, b = half_at(FLOOR_Z) - WALL_T, NOTCH - WALL_T
    feet = [f.bounds for f in mesure_feet()]
    for x, y in MESURE_HOLES:
        r = HOLE_D / 2
        assert max(abs(x), abs(y)) + r < a, (x, y)                    # dans le fond
        assert not (x + r > b and y + r > b), (x, y)                  # hors de l'échancrure
        for (x0, y0, _), (x1, y1, _) in feet:                         # hors des pieds
            dx, dy = max(x0 - x, 0, x - x1), max(y0 - y, 0, y - y1)
            assert np.hypot(dx, dy) > r + 0.3, (x, y)
    # Jeu autour du tube du trop-plein
    assert OVERFLOW_XY - OVERFLOW_R - NOTCH >= 1.0
    # Fentes des bouts de branche à plus de 3 mm des arêtes
    c = (b - a) / 2
    assert c + 3.5 + SLOT_W / 2 < b - 3.0 and c - 3.5 - SLOT_W / 2 > -a + 3.0


def main():
    assert SLOT_TOP < WATER_MAX_Z
    # Fentes à l'écart des arêtes : la fente extérieure doit rester dans la face la plus étroite.
    assert SLOT_PITCH + SLOT_W / 2 < half_at(FLOOR_Z) - WALL_T - 3.0
    # Trous d'angle hors des pieds (diagonale)
    assert np.hypot(FOOT_IN - HOLE_PITCH, FOOT_IN - HOLE_PITCH) > HOLE_D / 2

    check_mesure()

    for name, (m, n_holes, n_slots) in (("godet_semis_36x36x42.stl", make_godet()),
                                        ("godet_mesure_L_36x36x42.stl", make_godet_mesure())):
        assert m.is_volume and m.body_count == 1, name
        m.export(STL_DIR / name)
        e = m.extents
        area = n_holes * np.pi * HOLE_D ** 2 / 4
        print(f"{name} : {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm, {m.volume / 1000:.2f} cm3, "
              f"{n_holes} trous ({area:.0f} mm²), {n_slots} fentes")


if __name__ == "__main__":
    main()
