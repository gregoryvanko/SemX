#!/usr/bin/env python3
"""Cadre en bois de SemX V2 : bac à semis du commerce, réservoir dessous, panneaux LED réglables.

Quatre montants en tasseau servent à la fois de pieds et de colonnes pour l'éclairage.
Deux ceintures en tasseau entourent les montants : la ceinture basse porte les quatre
lattes du porte-bac, sur lesquelles repose le bac à semis ; le réservoir passe sous sa
traverse avant et se glisse sous le bac par l'avant. La ceinture haute relie le haut
des montants. Au-dessus, un cadre lumière reçoit les quatre panneaux
LED de V1, collés dessous. Il coulisse entre les montants et repose sur quatre
goupilles imprimées en 3D qui traversent les montants, percés tous les 30 mm.

Dépendances : pip install numpy trimesh manifold3d
Usage : python CAD/cadre_bois.py
Affiche la liste de débit, contrôle les jeux et écrit dans STL/ les pièces à imprimer
(goupille et support du boîtier de l'électronique, dans leur sens d'impression), et les vues d'assemblage, montée et éclatée, non destinées à l'impression.

Repère : x selon la longueur du bac (gauche-droite), y selon sa largeur (y < 0 à
l'avant, côté ouvert), z vers le haut depuis la table. Unités : mm.
"""
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent.parent
STL_DIR = ROOT / "STL"

# ── Bac à semis du commerce (mesuré) ───────────────────────────────────────────
BAC_IN_BOTTOM = (340.0, 205.0)    # intérieur, au fond
BAC_IN_TOP = (355.0, 220.0)       # intérieur, en haut
BAC_OUT_TOP = (375.0, 240.0)      # extérieur, rebord compris
BAC_H = 60.0
BAC_WALL = 2.0                    # épaisseur supposée de la paroi et du fond
BAC_RIM_T = 3.0                   # épaisseur supposée du rebord

# ── Réservoir d'eau (mesuré) ───────────────────────────────────────────────────
RES = (255.0, 184.0, 140.0)
RES_WALL = 3.0

# ── Panneaux LED (ceux de V1) et adhésif 3M ────────────────────────────────────
PANEL_L, PANEL_W, PANEL_T = 300.0, 80.0, 1.0
PANEL_N = 4
PANEL_GAP = 8.0                   # écart entre deux panneaux voisins
TAPE_L, TAPE_W, TAPE_T = 30.0, 50.0, 1.0

# ── Bois ───────────────────────────────────────────────────────────────────────
TW, TL = 20.0, 40.0               # section des tasseaux rabotés : 20 × 40 mm
# Montants : 20 mm en x (traversés par les goupilles), 40 mm en y.
# Ceintures et côtés du cadre lumière sur chant (40 mm en z), lattes et barres à plat (40 mm en y).
CLEAR_UNDER = 150.0               # hauteur libre sous la ceinture basse, pour faire passer le réservoir
BAC_CLEAR = (10.0, 5.0)           # jeu autour du rebord du bac : contre les montants en x, jusqu'aux lattes en y
FRAME_CLEAR = 1.0                 # jeu par côté entre le cadre lumière et les montants
LEG_H = 660.0                     # la ceinture haute reste au-dessus du cadre lumière

# En x, le bac entre entre les montants avec son rebord. En y, l'extérieur des montants
# est aligné sur les bouts des panneaux LED : les montants sont au-delà du bac en x,
# le rebord du bac peut donc dépasser leur face intérieure en y.
IN_X = BAC_OUT_TOP[0] + 2 * BAC_CLEAR[0]          # 395
OUT_Y = PANEL_L                                   # 300
IN_Y = OUT_Y - 2 * TL                             # 220, entre les montants avant et arrière
PLATE_Y = BAC_OUT_TOP[1] + 2 * BAC_CLEAR[1]       # 250, profondeur utile sous le bac, pour placer le réservoir
LEG_X = IN_X / 2 + TW / 2                         # axe des montants
LEG_Y = IN_Y / 2 + TL / 2
OUT_X = IN_X + 2 * TW

LOW_BELT_Z = CLEAR_UNDER                          # dessous de la ceinture basse
PLATE_Z = LOW_BELT_Z + TL                         # dessous des lattes, posées sur la ceinture basse
BAC_Z = PLATE_Z + TW                              # dessous du bac, posé sur les lattes
BAC_TOP = BAC_Z + BAC_H

# Réservoir : centré en x, vers l'avant.
RES_Y0 = -PLATE_Y / 2 + 5.0

# Porte-bac : lattes à plat selon x, posées sur les ceintures basses latérales, entre les montants
# avant et arrière.
# Les lattes extérieures arrivent au bord du fond du bac ; entre les deux lattes du
# milieu, une fente laisse passer le trop-plein.
BAC_BOTTOM_OUT = (BAC_IN_BOTTOM[0] + 2 * BAC_WALL, BAC_IN_BOTTOM[1] + 2 * BAC_WALL)
DRAIN_GAP = 40.0                  # fente centrale entre les deux lattes du milieu
SLAT_Y = (DRAIN_GAP / 2 + TL / 2, BAC_BOTTOM_OUT[1] / 2 - TL / 2)   # axes des lattes, de chaque côté de y = 0

# Trop-plein : passe-cloison dans le fond du bac, dans la fente centrale, au-dessus du réservoir.
DRAIN_D = 30.0                    # encombrement de l'écrou du passe-cloison
DRAIN_XY = (-110.0, 0.0)

# ── Cadre lumière et goupilles ─────────────────────────────────────────────────
FRAME_SIDE_X = (IN_X / 2 - FRAME_CLEAR - TW, IN_X / 2 - FRAME_CLEAR)   # côtés, contre les montants
FRAME_SIDE_L = OUT_Y                                                  # au ras de l'extérieur des montants
FRAME_BAR_L = 2 * FRAME_SIDE_X[1]                                     # barres, posées sur les côtés
FRAME_BAR_Y = PANEL_L / 2 - TL                                        # bord intérieur des barres
HOLE_D = 8.0                      # trous des montants et des côtés du cadre lumière
# Goupille imprimée à plat, couches dans le sens de la tige pour résister au cisaillement.
PIN_D = 7.7                       # 0,15 mm de jeu par côté dans le trou de Ø 8
PIN_FLAT = 0.5                    # méplat posé sur le plateau d'impression
PIN_L = 38.0                      # sous la tête : montant 20 + jeu 1 + 17 dans le côté du cadre
PIN_TIP = 1.0                     # chanfrein de la pointe
PIN_HEAD = (10.0, 16.0)           # poignée : longueur hors du montant, largeur (butée contre le montant)
PETG_DENSITY = 1.27e-3            # g/mm³
HOLE_PITCH = 30.0
FRAME_Z = np.arange(280.0, 551.0, HOLE_PITCH)     # dessous des côtés du cadre lumière, une position par trou
HERO_FRAME_Z = 340.0

# ── Boîtier de l'électronique (celui de V1) et son support imprimé ──────────────
# Le boîtier est debout au coin arrière droit, son dessus au niveau du haut du bac : hors
# de l'emprise du bac (pas de goutte), loin de l'avant (passage du réservoir) et des trous
# des goupilles. Il se glisse par le haut dans un support imprimé en U, sans vis : plaque
# contre la ceinture basse arrière, deux joues dont les lèvres retiennent le couvercle,
# et une butée en bas. La plaque est vissée sur la ceinture basse arrière. Encoche des
# câbles en bas.
BOX_STL = ROOT.parent / "V1" / "STL" / "Electronique boitier.stl"
LID_STL = ROOT.parent / "V1" / "STL" / "Electronique couvercle.stl"
BOX = (100.0, 125.0, 61.4)        # boîtier de V1 : x, y, z dans son STL (fond compris)
BOX_FLOOR = 1.4                   # épaisseur du fond, sous z = 0 dans son STL
BOX_LY_C = 52.5                   # milieu du boîtier en y dans son STL
LID_DROP = 50.0                   # le couvercle de V1 est enregistré 50 mm au-dessus de sa place
LID_T = 1.4                       # le couvercle dépasse de 1,4 mm au-dessus du boîtier
BOX_NOTCH = (-35.0, -20.0)        # encoche des câbles : x dans le STL, en haut de la paroi y max
BOX_TOP_Z = BAC_TOP               # dessus du boîtier au niveau du haut du bac
BRK_T = 3.0                       # épaisseur de la plaque et des joues
BRK_CLEAR = 0.5                   # jeu du boîtier dans la glissière, par côté
BRK_LIP = 5.0                     # lèvres des joues, devant le couvercle
BRK_STOP = (4.0, 30.0)            # butée sous le boîtier : épaisseur, profondeur (laisse l'encoche libre)
BRK_WINDOW_MARGIN = 8.0          # matière gardée autour des fenêtres en losange
BRK_WOOD_SCREW = (4.5, 8.5)       # vis à bois 4 × 25 : perçage, fraisure
BRK_HEAD_POCKET = (11.0, 2.5)     # creux au dos pour les têtes des vis des ceintures : Ø, profondeur
BRK_Y0 = OUT_Y / 2 + TW           # face extérieure de la ceinture basse arrière
BRK_X1 = OUT_X / 2 + TW           # face extérieure de la ceinture basse droite
BOX_Y0 = BRK_Y0 + BRK_T + BRK_CLEAR              # dessous du fond du boîtier
BOX_XC = BRK_X1 - BRK_CLEAR - BOX[0] / 2         # boîtier contre la joue droite, au ras du côté du cadre
BOX_ZC = BOX_TOP_Z - BOX[1] / 2                  # milieu du boîtier en hauteur
BOX_FRONT = BOX_Y0 + BOX[2] + LID_T              # face extérieure du couvercle
# Vis du support : deux dans la ceinture basse arrière, loin des vis de la ceinture.
BRK_SCREWS_BACK = [(BOX_XC - 35.0, LOW_BELT_Z + TL / 2), (BOX_XC, LOW_BELT_Z + TL / 2)]

# Panneaux : axe selon y, répartis en x sous les barres.
PANEL_X = (np.arange(PANEL_N) - (PANEL_N - 1) / 2) * (PANEL_W + PANEL_GAP)


def box(x0, x1, y0, y1, z0, z1):
    m = trimesh.creation.box(extents=(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)))
    m.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return m


def frustum(bottom, top, z0, z1):
    """Tronc de pyramide rectangulaire, du rectangle bottom en z0 au rectangle top en z1."""
    pts = []
    for (w, d), z in ((bottom, z0), (top, z1)):
        pts += [(sx * w / 2, sy * d / 2, z) for sx in (-1, 1) for sy in (-1, 1)]
    return trimesh.convex.convex_hull(np.array(pts))


def make_bac():
    """Bac évasé à paroi mince, avec un rebord plat en haut."""
    out_bottom = (BAC_IN_BOTTOM[0] + 2 * BAC_WALL, BAC_IN_BOTTOM[1] + 2 * BAC_WALL)
    out_top = (BAC_IN_TOP[0] + 2 * BAC_WALL, BAC_IN_TOP[1] + 2 * BAC_WALL)
    body = frustum(out_bottom, out_top, 0, BAC_H)
    rim = box(-BAC_OUT_TOP[0] / 2, BAC_OUT_TOP[0] / 2, -BAC_OUT_TOP[1] / 2, BAC_OUT_TOP[1] / 2,
              BAC_H - BAC_RIM_T, BAC_H)
    cavity = frustum(BAC_IN_BOTTOM, BAC_IN_TOP, BAC_WALL, BAC_H + 1e-3)
    m = trimesh.boolean.union([body, rim], engine="manifold")
    m = trimesh.boolean.difference([m, cavity], engine="manifold")
    m.apply_translation((0, 0, BAC_Z))
    return m


def make_reservoir():
    x0, y0 = -RES[0] / 2, RES_Y0
    outer = box(x0, -x0, y0, y0 + RES[1], 0, RES[2])
    inner = box(x0 + RES_WALL, -x0 - RES_WALL, y0 + RES_WALL, y0 + RES[1] - RES_WALL, RES_WALL, RES[2] + 1)
    return trimesh.boolean.difference([outer, inner], engine="manifold")


def led_face(frame_z):
    """Hauteur de la face LED : panneaux collés sous les barres, posées sur les côtés."""
    return frame_z + TL - TAPE_T - PANEL_T


def leg_hole_z(frame_z):
    return frame_z + TL / 2


def make_leg(sx, sy):
    x, y = sx * LEG_X, sy * LEG_Y
    leg = box(x - TW / 2, x + TW / 2, y - TL / 2, y + TL / 2, 0, LEG_H)
    holes = [trimesh.creation.cylinder(radius=HOLE_D / 2, height=TW + 2, sections=24,
                                       transform=trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
             .apply_translation((x, y, leg_hole_z(z))) for z in FRAME_Z]
    return trimesh.boolean.difference([leg] + holes, engine="manifold")


def make_slats():
    """Lattes du porte-bac, à plat, au ras de l'extérieur de la ceinture basse."""
    x = OUT_X / 2 + TW
    return [box(-x, x, s * y - TL / 2, s * y + TL / 2, PLATE_Z, PLATE_Z + TW)
            for y in SLAT_Y for s in (-1, 1)]


def make_light_frame(z):
    """Cadre lumière : deux côtés selon y, percés pour les goupilles, et deux barres selon x posées dessus."""
    x0, x1 = FRAME_SIDE_X
    sides, bars = [], []
    for s in (-1, 1):
        side = box(s * x0, s * x1, -FRAME_SIDE_L / 2, FRAME_SIDE_L / 2, z, z + TL)
        holes = [trimesh.creation.cylinder(radius=HOLE_D / 2, height=TW + 2, sections=24,
                                           transform=trimesh.transformations.rotation_matrix(np.pi / 2, (0, 1, 0)))
                 .apply_translation((s * (x0 + x1) / 2, sy * LEG_Y, leg_hole_z(z))) for sy in (-1, 1)]
        sides.append(trimesh.boolean.difference([side] + holes, engine="manifold"))
        bars.append(box(-x1, x1, s * FRAME_BAR_Y, s * (FRAME_BAR_Y + TL), z + TL, z + TL + TW))
    return sides, bars


def make_panels(z):
    """Panneaux LED vers le bas, collés sous les barres par un adhésif à chaque bout."""
    tapes, panels = [], []
    top = z + TL - TAPE_T
    for x in PANEL_X:
        panels.append(box(x - PANEL_W / 2, x + PANEL_W / 2, -PANEL_L / 2, PANEL_L / 2, top - PANEL_T, top))
        for s in (-1, 1):
            yc = s * (PANEL_L / 2 - TAPE_L / 2 - 2)
            tapes.append(box(x - TAPE_W / 2, x + TAPE_W / 2, yc - TAPE_L / 2, yc + TAPE_L / 2, top, z + TL))
    return tapes, panels


def make_pin():
    """Goupille posée sur son méplat (z = 0), tige selon +x, poignée en x < 0."""
    r = PIN_D / 2
    a = np.radians(np.arange(0, 360, 7.5))

    def profile(rr, x):
        pts = {(round(rr * np.cos(t), 4), round(max(rr * np.sin(t), PIN_FLAT - r), 4)) for t in a}
        return [(x, py, pz + r - PIN_FLAT) for py, pz in pts]

    tip = r - PIN_TIP
    shank = trimesh.convex.convex_hull(np.array(profile(r, -0.5) + profile(r, PIN_L - PIN_TIP)
                                                + profile(tip, PIN_L)))
    hl, hw = PIN_HEAD
    head = box(-hl, 0, -hw / 2, hw / 2, 0, PIN_D - PIN_FLAT)
    return trimesh.boolean.union([shank, head], engine="manifold")


def make_pins(z, pin=None):
    """Goupilles en place : poignée contre la face extérieure du montant, tige vers l'intérieur."""
    pin = make_pin() if pin is None else pin
    pins = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            m = pin.copy()
            m.apply_translation((0, 0, -(PIN_D / 2 - PIN_FLAT)))   # axe de la tige sur z = 0
            if sx > 0:
                m.apply_transform(trimesh.transformations.rotation_matrix(np.pi, (0, 0, 1)))
            m.apply_translation((sx * (IN_X / 2 + TW), sy * LEG_Y, leg_hole_z(z)))
            pins.append(m)
    return pins


def make_belt(z0):
    """Ceinture autour des quatre montants, dessous à z0 : traverses avant et arrière contre les
    faces extérieures, débordant pour couvrir les bouts des traverses latérales, elles-mêmes
    contre les faces extérieures gauche et droite. Toutes sur chant.
    Ordre : avant, arrière, gauche, droite."""
    x, y = OUT_X / 2, OUT_Y / 2
    z1 = z0 + TL
    long_ = [box(-(x + TW), x + TW, s * y, s * (y + TW), z0, z1) for s in (-1, 1)]
    short = [box(s * x, s * (x + TW), -y, y, z0, z1) for s in (-1, 1)]
    return long_ + short


def make_top_frame():
    """Ceinture haute, au ras du haut des montants."""
    return make_belt(LEG_H - TL)


def make_low_belt():
    """Ceinture basse : porte les lattes, le réservoir passe sous sa traverse avant."""
    return make_belt(LOW_BELT_Z)


BELT_SCREW = (4.0, 40.0)          # vis de la ceinture : diamètre, longueur


def make_belt_screws(z0=None):
    """Vis d'une ceinture dont le dessous est à z0 (ceinture haute par défaut), rangées
    comme les traverses de make_belt() :
    deux vis par montant, et deux par bout de traverse latérale pour les traverses avant et arrière."""
    d, l = BELT_SCREW
    x, y = OUT_X / 2, OUT_Y / 2
    z0 = LEG_H - TL if z0 is None else z0
    zs = (z0 + TL / 2 - 10, z0 + TL / 2 + 10)

    def screw(p_out, axis):
        """Vis dont la tête affleure en p_out, enfoncée selon -axis."""
        axis = np.array(axis, dtype=float)
        rot = trimesh.geometry.align_vectors((0, 0, 1), axis)
        shank = trimesh.creation.cylinder(radius=d / 2, height=l, sections=16)
        shank.apply_translation((0, 0, -l / 2))
        head = trimesh.creation.cylinder(radius=d, height=1.5, sections=24)
        head.apply_translation((0, 0, -0.75))
        m = trimesh.util.concatenate([shank, head])
        m.apply_transform(rot)
        m.apply_translation(p_out)
        return m

    groups = []
    for s in (-1, 1):          # traverses avant et arrière
        pts = [(sx * LEG_X, z) for sx in (-1, 1) for z in zs] + [(sx * (x + TW / 2), z) for sx in (-1, 1) for z in zs]
        groups.append([screw((px, s * (y + TW), z), (0, s, 0)) for px, z in pts])
    for s in (-1, 1):          # traverses latérales
        groups.append([screw((s * (x + TW), sy * LEG_Y, z), (s, 0, 0)) for sy in (-1, 1) for z in zs])
    return groups


def box_transform():
    """Passe du repère du STL du boîtier de V1 au repère du cadre : boîtier debout, sa
    longueur (y du STL) à la verticale, la paroi de l'encoche (y max du STL) en bas, le fond
    contre la plaque et le couvercle vers +y."""
    m = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float)
    m[:3, 3] = (BOX_XC, BOX_Y0 + BOX_FLOOR, BOX_ZC + BOX_LY_C)
    return m


def make_box(lift=0.0):
    """Boîtier et couvercle de V1, fermés et en place (soulevés de lift)."""
    box = trimesh.load(BOX_STL, force="mesh")
    lid = trimesh.load(LID_STL, force="mesh").apply_translation((0, 0, -LID_DROP))
    t = box_transform()
    return [m.apply_transform(t).apply_translation((0, 0, lift)) for m in (box, lid)]


def _hole_y(x, z, y0, y1, d, dk=None):
    """Trou selon y entre y0 et y1, fraisé côté y1 si dk."""
    out = [box(x - d / 2, x + d / 2, y0 - 1, y1 + 1, z - d / 2, z + d / 2)]
    out[0] = trimesh.creation.cylinder(radius=d / 2, height=y1 - y0 + 2, sections=32,
                                       transform=trimesh.transformations.rotation_matrix(-np.pi / 2, (1, 0, 0)))
    out[0].apply_translation((x, (y0 + y1) / 2, z))
    if dk:
        cone = trimesh.creation.cone(radius=dk / 2, height=dk / 2, sections=32)
        cone.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, (1, 0, 0)))   # pointe vers -y
        cone.apply_translation((x, y1 + 0.01, z))
        out.append(cone)
    return out


def make_bracket():
    """Support à glissière du boîtier, en place, au coin arrière droit."""
    t, c = BRK_T, BRK_CLEAR
    bx0, bx1 = BOX_XC - BOX[0] / 2 - c, BRK_X1          # intérieur de la glissière en x
    z0 = BOX_TOP_Z - BOX[1] - BRK_STOP[0]
    z1 = BOX_TOP_Z
    y0 = BRK_Y0
    yf = BOX_FRONT + c                                   # arrière des lèvres
    st, sd = BRK_STOP
    parts = [
        box(bx0 - t, bx1 + t, y0, y0 + t, z0, z1),                                   # plaque
        box(bx0 - t, bx0, y0, yf + t, z0, z1),                                       # joue gauche
        box(bx1, bx1 + t, y0, yf + t, z0, z1),                                       # joue droite
        box(bx0 - 0.1, bx0 + BRK_LIP, yf, yf + t, z0, z1),                           # lèvre gauche
        box(bx1 - BRK_LIP, bx1 + 0.1, yf, yf + t, z0, z1),                           # lèvre droite
        box(bx0 - 0.1, bx1 + 0.1, y0 + t - 0.1, y0 + t + sd, z0, z0 + st),           # butée
    ]
    solid = trimesh.boolean.union(parts, engine="manifold")
    cuts = []
    d, dk = BRK_WOOD_SCREW
    for x, z in BRK_SCREWS_BACK:
        cuts += _hole_y(x, z, y0, y0 + t, d, dk)
    # creux pour les têtes des vis de la ceinture, au dos de la plaque
    pd, ph = BRK_HEAD_POCKET
    groups = make_belt_screws(LOW_BELT_Z)
    for m in groups[1]:                                   # ceinture arrière : têtes en y = BRK_Y0
        x, _, z = m.bounds.mean(axis=0)
        if bx0 - t - pd / 2 < x < bx1 + t + pd / 2:
            p = trimesh.creation.cylinder(radius=pd / 2, height=2 * ph, sections=32,
                                          transform=trimesh.transformations.rotation_matrix(-np.pi / 2, (1, 0, 0)))
            cuts.append(p.apply_translation((x, y0, z)))
    # fenêtres en losange, qui s'impriment debout sans support
    mg = BRK_WINDOW_MARGIN
    zb = LOW_BELT_Z + TL + mg                              # au-dessus des vis du support et des têtes
    cuts.append(_diamond("y", (bx0 + bx1) / 2, (zb + z1 - mg) / 2, bx1 - bx0 - 2 * mg, z1 - mg - zb, y0, y0 + t))
    for x in (bx0 - t, bx1):
        cuts.append(_diamond("x", (y0 + t + yf) / 2, (z0 + st + mg + z1 - mg) / 2, yf - y0 - t - 2 * mg,
                             z1 - z0 - st - 2 * mg, x, x + t))
    return trimesh.boolean.difference([solid] + cuts, engine="manifold")


def _diamond(axis, u, z, w, h, a0, a1):
    """Losange de largeur w et de hauteur h, centré en (u, z), percé selon axis entre a0 et a1."""
    pts = np.array([(u - w / 2, z), (u, z - h / 2), (u + w / 2, z), (u, z + h / 2)])
    from shapely.geometry import Polygon
    m = trimesh.creation.extrude_polygon(Polygon(pts), a1 - a0 + 2)      # extrudé selon +z du plan (u, z)
    if axis == "y":
        # plan (x, z) extrudé selon y : (u, v, w) -> (u, w, v)
        m.apply_transform(np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=float))
        m.apply_translation((0, a1 + 1, 0))
    else:
        # plan (y, z) extrudé selon x : (u, v, w) -> (w, u, v)
        m.apply_transform(np.array([[0, 0, 1, 0], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=float))
        m.apply_translation((a0 - 1, 0, 0))
    return m


def bracket_print(bracket):
    """Support debout, posé sur le bas de la plaque et des joues, pour l'impression :
    les parois sont verticales, sans surplomb."""
    m = bracket.copy()
    m.apply_translation(-m.bounds[0])
    return m


def assembly(frame_z=HERO_FRAME_Z):
    """Pièces en place, regroupées par type pour les colorer."""
    sides, bars = make_light_frame(frame_z)
    tapes, panels = make_panels(frame_z)
    return {
        "leg": [make_leg(sx, sy) for sx in (-1, 1) for sy in (-1, 1)],
        "rail": make_low_belt(),
        "top": make_top_frame(),
        "slat": make_slats(),
        "reservoir": [make_reservoir()],
        "bac": [make_bac()],
        "frame": sides + bars,
        "pin": make_pins(frame_z),
        "tape": tapes,
        "panel": panels,
        "bracket": [make_bracket()],
        "ebox": make_box(),
    }


CUT_LIST = [
    ("Montant", "tasseau 20 × 40", LEG_H, 4,
     f"{len(FRAME_Z)} trous Ø 8 traversant les 20 mm, au milieu de la face de 40"),
    ("Ceinture basse latérale", "tasseau 20 × 40", OUT_Y, 2, "sur chant, contre l'extérieur des montants"),
    ("Ceinture basse avant ou arrière", "tasseau 20 × 40", OUT_X + 2 * TW, 2, "sur chant, contre l'extérieur des montants"),
    ("Latte du porte-bac", "tasseau 20 × 40", OUT_X + 2 * TW, 4, "à plat, posée sur les ceintures basses latérales"),
    ("Côté du cadre lumière", "tasseau 20 × 40", FRAME_SIDE_L, 2,
     f"sur chant, 2 trous Ø 8 à {FRAME_SIDE_L / 2 - LEG_Y:.0f} mm des bouts"),
    ("Barre du cadre lumière", "tasseau 20 × 40", FRAME_BAR_L, 2, "à plat, posée sur les côtés"),
    ("Ceinture haute avant ou arrière", "tasseau 20 × 40", OUT_X + 2 * TW, 2, "sur chant, contre l'extérieur des montants"),
    ("Ceinture haute latérale", "tasseau 20 × 40", OUT_Y, 2, "sur chant, contre l'extérieur des montants"),
]


def piece_number(name):
    """Numéro de repère d'une pièce en bois : son rang dans la liste de débit, à partir de 1."""
    return [n for n, *_ in CUT_LIST].index(name) + 1


def check():
    """Contrôle les jeux de la conception et affiche les hauteurs utiles."""
    res_x = (-RES[0] / 2, RES[0] / 2)
    res_y = (RES_Y0, RES_Y0 + RES[1])
    ok = True

    def expect(cond, msg):
        nonlocal ok
        print(("  ok   " if cond else "  ÉCHEC ") + msg)
        ok &= cond

    print("Contrôles :")
    slat_edge = SLAT_Y[1] + TL / 2
    expect(abs(slat_edge - BAC_BOTTOM_OUT[1] / 2) < 0.1, f"lattes sous tout le fond du bac ({BAC_BOTTOM_OUT[1]:.0f} mm)")
    gaps = (DRAIN_GAP, SLAT_Y[1] - SLAT_Y[0] - TL)
    expect(max(gaps) <= DRAIN_GAP and min(gaps) >= 0, f"fond du bac porté : fentes de {gaps[1]:.1f} et {gaps[0]:.0f} mm")
    expect(OUT_Y == PANEL_L and FRAME_SIDE_L == OUT_Y and FRAME_BAR_Y + TL == PANEL_L / 2,
           "montants, côtés et barres du cadre lumière au ras des bouts des panneaux")
    expect(RES[2] <= LOW_BELT_Z - 10, f"réservoir sous la ceinture basse avant : {LOW_BELT_Z - RES[2]:.0f} mm de marge en hauteur")
    expect(res_x[1] < IN_X / 2, f"réservoir entre les montants : {IN_X / 2 - res_x[1]:.1f} mm de chaque côté")
    expect(res_y[1] < OUT_Y / 2, f"réservoir dans la profondeur des montants : {OUT_Y / 2 - res_y[1]:.0f} mm à l'arrière")
    expect(SLAT_Y[1] + TL / 2 < LEG_Y - TL / 2, f"lattes entre les montants avant et arrière : "
           f"{LEG_Y - TL / 2 - SLAT_Y[1] - TL / 2:.1f} mm de jeu")
    expect(abs(DRAIN_XY[0]) + DRAIN_D / 2 < RES[0] / 2 and res_y[0] < DRAIN_XY[1] - DRAIN_D / 2
           and DRAIN_XY[1] + DRAIN_D / 2 < res_y[1], "trop-plein au-dessus du réservoir")
    expect(abs(DRAIN_XY[0]) + DRAIN_D / 2 < BAC_IN_BOTTOM[0] / 2 - 10
           and abs(DRAIN_XY[1]) + DRAIN_D / 2 < BAC_IN_BOTTOM[1] / 2 - 10, "trop-plein sous le fond du bac")
    expect(abs(DRAIN_XY[1]) + DRAIN_D / 2 <= DRAIN_GAP / 2, "trop-plein dans la fente entre les lattes du milieu")
    outer_panel = abs(PANEL_X[-1]) + PANEL_W / 2
    expect(outer_panel < IN_X / 2 - 5, f"panneaux entre les montants : {IN_X / 2 - outer_panel:.1f} mm de jeu")
    expect(outer_panel <= BAC_IN_TOP[0] / 2, f"panneaux au-dessus du bac : {2 * outer_panel:.0f} mm "
           f"couverts sur {BAC_IN_TOP[0]:.0f}")
    low = led_face(FRAME_Z[0]) - BAC_TOP
    expect(FRAME_Z[0] - BAC_TOP >= 10, f"côtés du cadre lumière à {FRAME_Z[0] - BAC_TOP:.0f} mm au-dessus du rebord du bac")
    side_gap = FRAME_SIDE_X[0] - outer_panel
    expect(side_gap >= 3, f"panneaux entre les côtés du cadre lumière : {side_gap:.1f} mm de jeu")
    pin_in = PIN_L - TW - FRAME_CLEAR
    expect(8 <= pin_in < TW - 1, f"goupille engagée de {pin_in:.0f} mm dans le côté du cadre lumière, épais de {TW:.0f} mm")
    expect(min(PIN_HEAD[1], PIN_D - PIN_FLAT) < HOLE_D < PIN_HEAD[1], "poignée plus large que le trou : butée contre le montant")
    expect(leg_hole_z(FRAME_Z[-1]) + 20 < LEG_H, "dernier trou à plus de 20 mm du haut des montants")
    light_top = FRAME_Z[-1] + TL + TW
    belt_z = LEG_H - TL
    expect(light_top <= belt_z - 10, f"cadre lumière, au plus haut, {belt_z - light_top:.0f} mm sous la ceinture haute")
    expect(leg_hole_z(FRAME_Z[-1]) + PIN_D / 2 + 10 < belt_z, f"goupille du trou le plus haut {belt_z - leg_hole_z(FRAME_Z[-1]) - PIN_D / 2:.0f} mm sous la ceinture haute")
    expect(2 * FRAME_SIDE_X[1] < IN_X, f"cadre lumière glissé par l'avant entre les montants : "
           f"{2 * FRAME_SIDE_X[1]:.0f} mm pour {IN_X:.0f} mm de passage")
    box_bottom = BOX_TOP_Z - BOX[1] - BRK_STOP[0]
    expect(abs(BOX_ZC + BOX[1] / 2 - BAC_TOP) < 0.01, f"dessus du boîtier au niveau du haut du bac ({BAC_TOP:.0f} mm)")
    expect(box_bottom <= LOW_BELT_Z and BOX_TOP_Z >= LOW_BELT_Z + TL,
           f"plaque du support sur toute la hauteur de la ceinture basse : de {box_bottom:.0f} à {BOX_TOP_Z:.0f} mm")
    expect(BRK_Y0 > BAC_OUT_TOP[1] / 2, f"boîtier hors de l'emprise du bac : {BRK_Y0 - BAC_OUT_TOP[1] / 2:.0f} mm derrière son rebord")
    pin_low = leg_hole_z(FRAME_Z[0]) - PIN_D / 2
    expect(BOX_TOP_Z < pin_low - 10, f"support {pin_low - BOX_TOP_Z:.0f} mm sous les goupilles les plus basses")
    notch_y = BOX_Y0 + BOX_FLOOR + 50.0                    # l'encoche commence 50 mm au-dessus du fond
    stop_y = BRK_Y0 + BRK_T + BRK_STOP[1]
    expect(stop_y < notch_y - 5, f"butée ({stop_y - BRK_Y0:.0f} mm de profondeur) loin de l'encoche des câbles")
    heads = [m.bounds.mean(axis=0) for g in make_belt_screws(LOW_BELT_Z) for m in g]
    own = [(x, BRK_Y0, z) for x, z in BRK_SCREWS_BACK]
    dmin = min(np.linalg.norm(np.array(o) - h) for o in own for h in heads)
    expect(dmin >= 15, f"vis du support à {dmin:.0f} mm au moins des vis de la ceinture basse")
    print(f"Face LED au-dessus du bord du bac : {low:.0f} à "
          f"{led_face(FRAME_Z[-1]) - BAC_TOP:.0f} mm, {len(FRAME_Z)} positions tous les {HOLE_PITCH:.0f} mm")
    print(f"Trous des montants, axe à {', '.join(f'{leg_hole_z(z):.0f}' for z in FRAME_Z)} mm de la table")
    print(f"Encombrement : {OUT_X + 2 * TW:.0f} × {OUT_Y + 2 * TW:.0f} × {LEG_H:.0f} mm (ceinture comprise ; {OUT_X:.0f} × {OUT_Y:.0f} mm sous la ceinture) ; dessous du bac à {BAC_Z:.0f} mm")
    back = BOX_FRONT + BRK_CLEAR + BRK_T
    print(f"Avec le boîtier de l'électronique : {OUT_X / 2 + TW + BRK_X1 + BRK_T:.0f} × {OUT_Y / 2 + TW + back:.0f} mm au sol")
    return ok


def print_cut_list():
    print("Liste de débit :")
    for i, (name, mat, length, qty, note) in enumerate(CUT_LIST, 1):
        length = f"{length:.0f}" if isinstance(length, float) else length
        print(f"  [{i}] {qty} × {name:24s} {mat:20s} {length:>10s} mm  {note}")


def explode(groups):
    shifts = {"leg": (0, 0, 0), "rail": (0, 0, 0), "top": (0, 0, 300), "slat": (0, 0, 90), "reservoir": (0, -320, 0),
              "bac": (0, 0, 170), "frame": (0, 0, 420), "pin": (110, 0, 420), "tape": (0, 0, 370),
              "panel": (0, 0, 320), "bracket": (0, 80, 0), "ebox": (0, 170, 0)}
    out = {}
    for key, meshes in groups.items():
        dx, dy, dz = shifts[key]
        out[key] = [m.copy().apply_translation((np.sign(m.centroid[0]) * dx, dy, dz)) for m in meshes]
    return out


def main():
    print_cut_list()
    if not check():
        raise SystemExit("La conception ne passe pas les contrôles.")
    STL_DIR.mkdir(exist_ok=True)
    pin = make_pin()
    pin.export(STL_DIR / "goupille_cadre_lumiere.stl")
    print(f"Goupille : {pin.extents[0]:.1f} × {pin.extents[1]:.1f} × {pin.extents[2]:.1f} mm, "
          f"{pin.volume * PETG_DENSITY:.1f} g de PETG, étanche : {pin.is_watertight}")
    bracket = bracket_print(make_bracket())
    bracket.export(STL_DIR / "support_boitier.stl")
    print(f"Support du boîtier : {bracket.extents[0]:.0f} × {bracket.extents[1]:.0f} × {bracket.extents[2]:.0f} mm, "
          f"{bracket.volume * PETG_DENSITY:.0f} g de PETG, étanche : {bracket.is_watertight}")
    groups = assembly()
    trimesh.util.concatenate([m for ms in groups.values() for m in ms]).export(STL_DIR / "assemblage_v2_vue.stl")
    trimesh.util.concatenate([m for ms in explode(groups).values() for m in ms]).export(
        STL_DIR / "assemblage_v2_eclate_vue.stl")
    print(f"Vues écrites dans {STL_DIR}")


if __name__ == "__main__":
    main()
