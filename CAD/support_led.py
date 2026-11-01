#!/usr/bin/env python3
"""Support de panneaux LED à hauteur réglable pour SemiX, version quatre colonnes.

Génère les pièces imprimables dans STL/ et une vue d'assemblage.
Dépendances : pip install numpy scipy trimesh manifold3d shapely mapbox_earcut
Usage : python CAD/support_led.py [hauteur_sous_traverse_mm]
La hauteur de la vue doit être un cran : 195, 210, 225... jusqu'à 360.

Repère d'assemblage : z vers le haut, axe des panneaux selon x, colonnes
sur les faces x du réservoir, faces y libres. Unités : mm.
"""
import sys
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parent.parent
STL_DIR = ROOT / "STL"

# Panneaux LED
PANEL_L = 300.0
PANEL_W = 80.0
PANEL_T_VIEW = 4.0        # épaisseur pour la vue uniquement, la traverse est ouverte

# Réservoir
RESERVOIR_HALF = 100.6

# Colonne et coulisseaux
COL = 14.0
COL_CHAMFER = 0.8
FIT = 0.25                # jeu par côté colonne / coulisseau
SLEEVE_WALL = 3.0
SLEEVE_H = 32.0
BORE = COL + 2 * FIT
SLEEVE_OUT = BORE + 2 * SLEEVE_WALL
BAR_L = 320.0             # imprimée en diagonale sur le plateau du X1 Carbon

# Crémaillère : deux trous de coulisseau décalés de 15 mm sur un pas de 30 mm
# donnent un réglage tous les 15 mm.
HOLE_PITCH = 30.0
HOLE_D = 4.4
PIN_D = 4.0
PIN_FLAT = 0.4            # méplat de la goupille, posé sur le plateau
PIN_L = SLEEVE_OUT - 0.5
SLEEVE_HOLES = (9.0, 24.0)
RACK_HOLES = np.arange(149.0, 300.0, HOLE_PITCH)  # depuis le bas de la colonne

# Traverse : les deux panneaux centraux passent entre les colonnes, les deux
# autres à l'extérieur.
SEAT = 15.0               # longueur de panneau engagée dans la traverse
FLOOR = 3.0
LIP = 3.0                 # appui sous les grands côtés du panneau
LIP_END = 4.0             # appui sous le petit côté du panneau
WALL_H = 10.0
RIB_H = 8.0               # la nervure centrale ne fait que guider les panneaux
END_GAP = 0.5             # jeu en bout de panneau
END_WALL = 3.0
CENTER_RIB = 3.0
POCKET_W = 80.8
TRAVERSE_HALF = 158.0     # limité par la diagonale du plateau

# Pied d'une seule pièce par face : ses deux douilles garantissent l'écartement
# des colonnes, que deux pièces collées séparément ne tiendraient pas.
GLUE_T = 2.4
GLUE_H = 86.0             # s'arrête sous le joint réservoir / bac
ARCH = 78.0               # demi-largeur de l'évidement à 45°, imprimable sans support
POST_GAP = 0.4            # le fût ne touche pas le bac, qui reste amovible
FOOT_H = 110.0
COL_BOTTOM = 70.0

# Positions d'assemblage
COL_X = RESERVOIR_HALF + POST_GAP + SLEEVE_OUT / 2
COL_Y = CENTER_RIB / 2 + POCKET_W + SLEEVE_OUT / 2
PANEL_Y = (CENTER_RIB / 2 + POCKET_W / 2, COL_Y + SLEEVE_OUT / 2 + POCKET_W / 2)


def box(x0, x1, y0, y1, z0, z1):
    m = trimesh.creation.box(extents=(x1 - x0, y1 - y0, z1 - z0))
    m.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return m


def prism_z(points, z0, z1):
    m = trimesh.creation.extrude_polygon(Polygon(points), z1 - z0)
    m.apply_translation((0, 0, z0))
    return m


def prism_x(points_yz, x0, x1):
    m = trimesh.creation.extrude_polygon(Polygon(points_yz), x1 - x0)
    m.apply_transform(np.array([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1.0]]))
    return m


def prism_y(points_xz, y0, y1):
    m = trimesh.creation.extrude_polygon(Polygon(points_xz), y1 - y0)
    m.apply_transform(np.array([[1, 0, 0, 0], [0, 0, -1, y1], [0, 1, 0, 0], [0, 0, 0, 1.0]]))
    return m


def cyl_z(x, y, d, z0, z1):
    m = trimesh.creation.cylinder(radius=d / 2, height=z1 - z0, sections=48)
    m.apply_translation((x, y, (z0 + z1) / 2))
    return m


def teardrop_x(y, z, d, x0, x1):
    """Trou horizontal imprimable sans support : pointe à 45° vers le haut."""
    r = d / 2
    a = np.radians(np.arange(-225, 46, 7.5))
    pts = [(y + r * np.cos(t), z + r * np.sin(t)) for t in a]
    pts.append((y, z + r * np.sqrt(2)))
    return prism_x(pts, x0, x1)


def union(*meshes):
    return trimesh.boolean.union(list(meshes), engine="manifold")


def cut(mesh, *tools):
    return trimesh.boolean.difference([mesh, *tools], engine="manifold")


def frustum(x, y, half_big, half_small, z_big, z_small):
    pts = []
    for h, z in ((half_big, z_big), (half_small, z_small)):
        pts += [(x + sx * h, y + sy * h, z) for sx in (-1, 1) for sy in (-1, 1)]
    return trimesh.convex.convex_hull(np.array(pts))


def make_bar():
    """Colonne d'un seul tenant : longueur selon x, trous verticaux."""
    c = COL_CHAMFER
    a = COL
    section = [(c, 0), (a - c, 0), (a, c), (a, a - c), (a - c, a), (c, a), (0, a - c), (0, c)]
    bar = prism_x(section, 0, BAR_L)
    return cut(bar, *[cyl_z(x, a / 2, HOLE_D, -1, a + 1) for x in RACK_HOLES])


def make_pin():
    """Goupille à poignée, imprimée à plat pour résister au cisaillement."""
    r = PIN_D / 2
    a = np.radians(np.arange(0, 360, 7.5))
    pts = [(r * np.cos(t), max(r * np.sin(t), PIN_FLAT - r) + r - PIN_FLAT) for t in a]
    pts = [p for i, p in enumerate(pts) if p != pts[i - 1]]
    shaft = prism_x(pts, 0, PIN_L)
    head = box(-8, 0, -7, 7, 0, PIN_D - PIN_FLAT)
    taper = [prism_z([(PIN_L - 3, s * (r + 0.5)), (PIN_L + 1, s * (r + 0.5)), (PIN_L + 1, s * (r - 1.0)),
                      (PIN_L - 3, s * r)][::s], -1, 6) for s in (-1, 1)]
    return union(cut(shaft, *taper), head)


def make_traverse():
    """Traverse côté x>0, en coordonnées d'assemblage, z=0 sur le plateau."""
    end0 = PANEL_L / 2 + END_GAP
    end1 = end0 + END_WALL
    seat0 = PANEL_L / 2 - SEAT
    half = SLEEVE_OUT / 2

    parts = [box(end0, end1, -TRAVERSE_HALF, TRAVERSE_HALF, 0, WALL_H),
             box(PANEL_L / 2 - LIP_END, end0, -TRAVERSE_HALF, TRAVERSE_HALF, 0, FLOOR),
             box(seat0, end0, -CENTER_RIB / 2, CENTER_RIB / 2, 0, RIB_H),
             box(seat0, end0, -CENTER_RIB / 2 - LIP, CENTER_RIB / 2 + LIP, 0, FLOOR)]
    tools = []
    for s in (-1, 1):
        y = s * COL_Y
        parts += [box(COL_X - half, COL_X + half, y - half, y + half, 0, SLEEVE_H),
                  box(COL_X, end0, y - half, y + half, 0, WALL_H),
                  box(seat0, end0, y - half - LIP, y + half + LIP, 0, FLOOR),
                  prism_y([(COL_X + half - 1, WALL_H), (COL_X + half - 1, SLEEVE_H), (end0, WALL_H)],
                          y - 2.4, y + 2.4)]
        tools += [box(COL_X - BORE / 2, COL_X + BORE / 2, y - BORE / 2, y + BORE / 2, -1, SLEEVE_H + 1),
                  frustum(COL_X, y, BORE / 2 + 0.8, BORE / 2, -0.2, 0.8)]
        # Trous borgnes : la goupille entre côté bac et s'arrête contre le renfort
        tools += [teardrop_x(y, z, HOLE_D, COL_X - half - 1, COL_X + half) for z in SLEEVE_HOLES]
    return cut(union(*parts), *tools)


def make_foot():
    """Pied côté x>0, en coordonnées d'assemblage. Le dos en x0 se colle au réservoir."""
    half = SLEEVE_OUT / 2
    x0 = RESERVOIR_HALF
    w = COL_Y + half
    plate = prism_x([(-w, 0), (w, 0), (w, GLUE_H), (-w, GLUE_H)], x0, x0 + GLUE_T)
    parts = [cut(plate, prism_x([(-ARCH - 1, -1), (ARCH + 1, -1), (0, ARCH)], x0 - 1, x0 + GLUE_T + 1))]
    tools = []
    for s in (-1, 1):
        y = s * COL_Y
        parts.append(box(COL_X - half, COL_X + half, y - half, y + half, 0, FOOT_H))
        tools.append(box(COL_X - BORE / 2, COL_X + BORE / 2, y - BORE / 2, y + BORE / 2, COL_BOTTOM, FOOT_H + 1))
    return cut(union(*parts), *tools)


# Colonne : longueur -> z, trous -> x
BAR_TO_WORLD = np.array([[0, 0, 1, 0], [0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1.0]])
ROT_180 = trimesh.transformations.rotation_matrix(np.pi, (0, 0, 1))


def placed(mesh, *matrices):
    m = mesh.copy()
    for t in matrices:
        m.apply_transform(t)
    return m


def tr(x, y, z):
    return trimesh.transformations.translation_matrix((x, y, z))


def sleeve_hole_for(z_traverse):
    for h in SLEEVE_HOLES:
        if np.isclose(RACK_HOLES, z_traverse + h - COL_BOTTOM).any():
            return h
    raise ValueError(f"{z_traverse} ne tombe pas sur un cran")


def assembly(parts, z_traverse):
    """Retourne les pièces positionnées, côté droit puis côté gauche."""
    groups = {"foot": [], "bar": [], "traverse": [], "panel": [], "pin": []}
    half = SLEEVE_OUT / 2
    lift = tr(0, 0, -PIN_D / 2 + PIN_FLAT)
    hole = sleeve_hole_for(z_traverse)
    for side in (np.eye(4), ROT_180):
        groups["foot"].append(placed(parts["foot"], side))
        groups["traverse"].append(placed(parts["traverse"], tr(0, 0, z_traverse), side))
        for sy in (-1, 1):
            y = sy * COL_Y
            groups["bar"].append(placed(parts["bar"], tr(0, -COL / 2, -COL / 2), BAR_TO_WORLD,
                                        tr(COL_X, y, COL_BOTTOM), side))
            groups["pin"].append(placed(parts["pin"], lift, tr(COL_X - half - 0.2, y, z_traverse + hole), side))
    for y in (-PANEL_Y[1], -PANEL_Y[0], PANEL_Y[0], PANEL_Y[1]):
        groups["panel"].append(box(-PANEL_L / 2, PANEL_L / 2, y - PANEL_W / 2, y + PANEL_W / 2,
                                   z_traverse + FLOOR, z_traverse + FLOOR + PANEL_T_VIEW))
    return groups


def on_bed(mesh, angle=0.0):
    """Pose la pièce sur le plateau, tournée si elle ne tient qu'en diagonale."""
    m = mesh.copy()
    if angle:
        m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(angle), (0, 0, 1)))
    centre = (m.bounds[0] + m.bounds[1]) / 2
    m.apply_translation((128 - centre[0], 128 - centre[1], -m.bounds[0][2]))
    return m


def build_parts():
    return {
        "foot": make_foot(),
        "bar": make_bar(),
        "traverse": make_traverse(),
        "pin": make_pin(),
    }


def main():
    z_traverse = float(sys.argv[1]) if len(sys.argv) > 1 else 270.0
    parts = build_parts()
    on_bed(parts["foot"]).export(STL_DIR / "support_led_pied.stl")
    # Diagonale opposée à la zone exclue de l'avant gauche du plateau
    on_bed(parts["bar"], -45).export(STL_DIR / "support_led_colonne.stl")
    on_bed(parts["traverse"], 45).export(STL_DIR / "support_led_traverse.stl")
    on_bed(parts["pin"]).export(STL_DIR / "support_led_goupille.stl")
    groups = assembly(parts, z_traverse)
    base = trimesh.load(STL_DIR / "assemblage_v12_vue.stl", force="mesh")
    trimesh.util.concatenate([base] + [m for g in groups.values() for m in g]).export(
        STL_DIR / "assemblage_support_led_vue.stl")


if __name__ == "__main__":
    main()
