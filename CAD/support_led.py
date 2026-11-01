#!/usr/bin/env python3
"""Support de panneaux LED à hauteur réglable pour SemiX, version quatre colonnes.

Génère les pièces imprimables dans STL/ et une vue d'assemblage.
Dépendances : pip install numpy scipy trimesh manifold3d shapely mapbox_earcut
Usage : python CAD/support_led.py [hauteur_sous_traverse_mm]
La hauteur de la vue doit être un cran : 198, 213, 228... jusqu'à 363.

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
PANEL_T = 1.0
TAPE_L = 30.0             # adhésif double face 3M, selon la longueur du panneau
TAPE_W = 50.0
TAPE_T = 1.0              # épaisseur supposée, pour la vue et le calcul des hauteurs

# Réservoir
RESERVOIR_HALF = 100.6

# Colonne et coulisseaux
COL = 14.0
COL_CHAMFER = 0.8
FIT = 0.25                # jeu par côté colonne / coulisseau
SLEEVE_WALL = 3.0
SLEEVE_H = 30.0
BORE = COL + 2 * FIT
SLEEVE_OUT = BORE + 2 * SLEEVE_WALL
BAR_L = 320.0             # imprimée en diagonale sur le plateau du X1 Carbon

# Nervures d'écrasement en bas de colonne, pour supprimer le jeu dans le fût du pied.
# Deux zones, aux extrémités de l'emboîtement, sur trois faces : la quatrième est
# posée sur le plateau et reste plaquée contre le fût.
CRUSH = 0.1               # serrage validé sur une pièce imprimée
CRUSH_ZONES = ((3.0, 11.0), (29.0, 37.0))  # depuis le bas de la colonne
CRUSH_W = 3.0
CRUSH_RAMP = 1.5

# Crémaillère : deux trous de coulisseau décalés de 15 mm sur un pas de 30 mm
# donnent un réglage tous les 15 mm.
HOLE_PITCH = 30.0
HOLE_D = 4.4
PIN_D = 4.0
PIN_FLAT = 0.4            # méplat de la goupille, posé sur le plateau
STRUT_TAB = 3.0           # patte d'entretoise, traversée par la goupille
PIN_L = SLEEVE_OUT - 0.5 + STRUT_TAB
SLEEVE_HOLES = (6.0, 21.0)
RACK_HOLES = np.arange(149.0, 300.0, HOLE_PITCH)  # depuis le bas de la colonne

# Traverse : les panneaux, LED vers le bas, sont collés sous sa bande continue,
# qui forme une cornière avec la paroi.
# Les colonnes passent entre les panneaux, le coulisseau reste au-dessus d'eux.
PAD_T = 2.4
PAD_MARGIN = 1.0          # débord de la bande de chaque côté de l'adhésif
WALL_H = 10.0
WALL_T = 3.0
RIB_T = 2.4               # nervure à chaque adhésif, pour que la bande ne fléchisse pas
RIB_H = 6.0
TRAVERSE_HALF = 158.0     # limité par la diagonale du plateau
CENTER_GAP = 2.0          # écart entre les deux panneaux centraux
PANEL_CLEAR = 1.5         # écart entre une colonne et le panneau extérieur

# Entretoise : relie deux coulisseaux face à face, au-dessus des panneaux. Son corps
# passe au-dessus des trous pour laisser la tête de goupille accessible.
STRUT_CLEAR = 0.3         # jeu par côté contre les coulisseaux
STRUT_Z0 = 24.0
STRUT_Z1 = 34.0
STRUT_W = 8.0

# Pied d'une seule pièce par face : ses deux douilles garantissent l'écartement
# des colonnes, que deux pièces collées séparément ne tiendraient pas.
GLUE_T = 2.4
GLUE_H = 86.0             # s'arrête sous le joint réservoir / bac
ARCH = 76.0               # demi-largeur de l'évidement à 45°, imprimable sans support
POST_GAP = 0.4            # le fût ne touche pas le bac, qui reste amovible
FOOT_INSET = 0.3          # retrait de chaque bout du pied, pour rester dans la largeur du réservoir
FOOT_H = 110.0
COL_BOTTOM = 70.0

# Positions d'assemblage
COL_X = RESERVOIR_HALF + POST_GAP + SLEEVE_OUT / 2
COL_Y = RESERVOIR_HALF - FOOT_INSET - SLEEVE_OUT / 2
PANEL_Y = (CENTER_GAP / 2 + PANEL_W / 2, COL_Y + COL / 2 + PANEL_CLEAR + PANEL_W / 2)
# Sur les panneaux extérieurs, l'adhésif est décalé vers l'intérieur : la traverse
# s'arrête avant le bord du panneau.
TAPE_Y = (PANEL_Y[0], TRAVERSE_HALF - PAD_MARGIN - TAPE_W / 2)
TAPE_X = PANEL_L / 2 - TAPE_L / 2


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


def crush_rib(x0, x1, height, normal):
    """Nervure en pente aux deux bouts, sur une face de la colonne, centrée sur la face."""
    a = COL
    w = CRUSH_W / 2
    r = CRUSH_RAMP
    top = 0.5                 # demi-largeur du sommet, qui s'écrase
    if normal == "z":
        pts = [(x, y, z) for x, z, half in ((x0, a - 0.3, w), (x1, a - 0.3, w), (x0 + r, a + height, top),
                                            (x1 - r, a + height, top))
               for y in (a / 2 - half, a / 2 + half)]
    else:
        side = a + height if normal > 0 else -height
        base = a - 0.3 if normal > 0 else 0.3
        pts = [(x, y, z) for x, y, half in ((x0, base, w), (x1, base, w), (x0 + r, side, top), (x1 - r, side, top))
               for z in (a / 2 - half, a / 2 + half)]
    return trimesh.convex.convex_hull(np.array(pts))


def make_bar():
    """Colonne d'un seul tenant : longueur selon x, trous verticaux."""
    c = COL_CHAMFER
    a = COL
    section = [(c, 0), (a - c, 0), (a, c), (a, a - c), (a - c, a), (c, a), (0, a - c), (0, c)]
    parts = [prism_x(section, 0, BAR_L)]
    for x0, x1 in CRUSH_ZONES:
        parts += [crush_rib(x0, x1, 2 * FIT + CRUSH, "z"), crush_rib(x0, x1, FIT + CRUSH, 1),
                  crush_rib(x0, x1, FIT + CRUSH, -1)]
    return cut(union(*parts), *[cyl_z(x, a / 2, HOLE_D, -1, a + 2) for x in RACK_HOLES])


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
    """Traverse côté x>0, en coordonnées d'assemblage.

    La face z=0 reçoit l'adhésif et repose sur le plateau à l'impression.
    """
    half = SLEEVE_OUT / 2
    pad_x0 = TAPE_X - TAPE_L / 2 - PAD_MARGIN
    pad_x1 = TAPE_X + TAPE_L / 2 + PAD_MARGIN
    wall0 = pad_x1 - WALL_T

    parts = [box(wall0, pad_x1, -TRAVERSE_HALF, TRAVERSE_HALF, 0, WALL_H),
             box(pad_x0, pad_x1, -TRAVERSE_HALF, TRAVERSE_HALF, 0, PAD_T)]
    tools = []
    for s in (-1, 1):
        for y in TAPE_Y:
            parts.append(box(pad_x0, wall0, s * y - RIB_T / 2, s * y + RIB_T / 2, 0, RIB_H))
        y = s * COL_Y
        parts += [box(COL_X - half, COL_X + half, y - half, y + half, 0, SLEEVE_H),
                  box(COL_X, wall0, y - half, y + half, 0, PAD_T),
                  prism_y([(COL_X + half - 1, PAD_T), (COL_X + half - 1, SLEEVE_H), (wall0 + 1, WALL_H),
                           (wall0 + 1, PAD_T)], y - 2.4, y + 2.4)]
        tools += [box(COL_X - BORE / 2, COL_X + BORE / 2, y - BORE / 2, y + BORE / 2, -1, SLEEVE_H + 1),
                  frustum(COL_X, y, BORE / 2 + 0.8, BORE / 2, -0.2, 0.8)]
        # Trous borgnes : la goupille entre côté bac et s'arrête contre le renfort
        tools += [teardrop_x(y, z, HOLE_D, COL_X - half - 1, COL_X + half) for z in SLEEVE_HOLES]
    return cut(union(*parts), *tools)


def make_strut():
    """Entretoise retournée pour l'impression : corps sur le plateau, pattes vers le haut."""
    half = SLEEVE_OUT / 2
    outer = COL_X - half - STRUT_CLEAR
    inner = outer - STRUT_TAB
    h = STRUT_Z1 - STRUT_Z0
    parts = [box(-outer, outer, -STRUT_W / 2, STRUT_W / 2, 0, h)]
    tools = []
    for s in (-1, 1):
        lo, hi = sorted((s * inner, s * outer))
        parts.append(box(lo, hi, -half, half, 0, STRUT_Z1))
        tools += [teardrop_x(0, STRUT_Z1 - z, HOLE_D, lo - 1, hi + 1) for z in SLEEVE_HOLES]
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
    groups = {"foot": [], "bar": [], "traverse": [], "strut": [], "tape": [], "panel": [], "pin": []}
    half = SLEEVE_OUT / 2
    lift = tr(0, 0, -PIN_D / 2 + PIN_FLAT)
    flip = trimesh.transformations.rotation_matrix(np.pi, (1, 0, 0))
    pin_x = COL_X - half - STRUT_CLEAR - STRUT_TAB - 0.2
    hole = sleeve_hole_for(z_traverse)
    for side in (np.eye(4), ROT_180):
        groups["foot"].append(placed(parts["foot"], side))
        groups["traverse"].append(placed(parts["traverse"], tr(0, 0, z_traverse), side))
        for sy in (-1, 1):
            y = sy * COL_Y
            groups["bar"].append(placed(parts["bar"], tr(0, -COL / 2, -COL / 2), BAR_TO_WORLD,
                                        tr(COL_X, y, COL_BOTTOM), side))
            groups["pin"].append(placed(parts["pin"], lift, tr(pin_x, y, z_traverse + hole), side))
    for sy in (-1, 1):
        groups["strut"].append(placed(parts["strut"], flip, tr(0, sy * COL_Y, z_traverse + STRUT_Z1)))
    panel_top = z_traverse - TAPE_T
    for sy in (-1, 1):
        for panel_y, tape_y in zip(PANEL_Y, TAPE_Y):
            y = sy * panel_y
            groups["panel"].append(box(-PANEL_L / 2, PANEL_L / 2, y - PANEL_W / 2, y + PANEL_W / 2,
                                       panel_top - PANEL_T, panel_top))
            for sx in (-1, 1):
                x = sx * TAPE_X
                yt = sy * tape_y
                groups["tape"].append(box(x - TAPE_L / 2, x + TAPE_L / 2, yt - TAPE_W / 2, yt + TAPE_W / 2,
                                          panel_top, z_traverse))
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
        "strut": make_strut(),
        "pin": make_pin(),
    }


def main():
    z_traverse = float(sys.argv[1]) if len(sys.argv) > 1 else 273.0
    parts = build_parts()
    on_bed(parts["foot"]).export(STL_DIR / "support_led_pied.stl")
    # Diagonale opposée à la zone exclue de l'avant gauche du plateau
    on_bed(parts["bar"], -45).export(STL_DIR / "support_led_colonne.stl")
    on_bed(parts["traverse"], 45).export(STL_DIR / "support_led_traverse.stl")
    on_bed(parts["strut"]).export(STL_DIR / "support_led_entretoise.stl")
    on_bed(parts["pin"]).export(STL_DIR / "support_led_goupille.stl")
    groups = assembly(parts, z_traverse)
    base = trimesh.load(STL_DIR / "assemblage_v12_vue.stl", force="mesh")
    trimesh.util.concatenate([base] + [m for g in groups.values() for m in g]).export(
        STL_DIR / "assemblage_support_led_vue.stl")


if __name__ == "__main__":
    main()
