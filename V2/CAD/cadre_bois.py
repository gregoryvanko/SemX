#!/usr/bin/env python3
"""Cadre en bois de SemX V2 : bac à semis du commerce, réservoir dessous, panneaux LED réglables.

Quatre montants en tasseau servent à la fois de pieds et de colonnes pour l'éclairage.
Un porte-bac de quatre lattes en tasseau, posées à plat sur deux traverses latérales,
porte le bac à semis à 150 mm au-dessus de la table : le réservoir se glisse dessous,
par l'avant, qui reste ouvert. Au-dessus, un cadre lumière reçoit les quatre panneaux
LED de V1, collés dessous. Il coulisse entre les montants et repose sur quatre
goupilles imprimées en 3D qui traversent les montants, percés tous les 30 mm.

Dépendances : pip install numpy trimesh manifold3d
Usage : python CAD/cadre_bois.py
Affiche la liste de débit, contrôle les jeux et écrit dans STL/ la goupille à imprimer,
posée sur son méplat, et les vues d'assemblage, montée et éclatée, non destinées à l'impression.

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
# Traverses et côtés du cadre lumière sur chant (40 mm en z), barres à plat (40 mm en y).
CLEAR_UNDER = 150.0               # hauteur libre sous le porte-bac, pour le réservoir
BAC_CLEAR = (10.0, 5.0)           # jeu autour du rebord du bac : contre les montants en x, jusqu'à la traverse arrière en y
FRAME_CLEAR = 1.0                 # jeu par côté entre le cadre lumière et les montants
LEG_H = 600.0

# En x, le bac entre entre les montants avec son rebord. En y, l'extérieur des montants
# est aligné sur les bouts des panneaux LED : les montants sont au-delà du bac en x,
# le rebord du bac peut donc dépasser leur face intérieure en y.
IN_X = BAC_OUT_TOP[0] + 2 * BAC_CLEAR[0]          # 395
OUT_Y = PANEL_L                                   # 300
IN_Y = OUT_Y - 2 * TL                             # 220, entre les montants avant et arrière
PLATE_Y = BAC_OUT_TOP[1] + 2 * BAC_CLEAR[1]       # 250, profondeur utile sous le bac (réservoir, traverse arrière)
LEG_X = IN_X / 2 + TW / 2                         # axe des montants
LEG_Y = IN_Y / 2 + TL / 2
OUT_X = IN_X + 2 * TW

PLATE_Z = CLEAR_UNDER                             # dessous des lattes du porte-bac
BAC_Z = PLATE_Z + TW                              # dessous du bac, posé sur les lattes
BAC_TOP = BAC_Z + BAC_H

# Réservoir : centré en x, vers l'avant, devant la traverse arrière.
RES_Y0 = -PLATE_Y / 2 + 5.0
BACK_RAIL_Y = (PLATE_Y / 2 - TW, PLATE_Y / 2)

# Porte-bac : lattes à plat selon x, d'un montant à l'autre, sur les traverses latérales.
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
FRAME_Z = np.arange(240.0, 511.0, HOLE_PITCH)     # dessous des côtés du cadre lumière, une position par trou
HERO_FRAME_Z = 300.0

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
    """Lattes du porte-bac, à plat, d'un montant à l'autre."""
    return [box(-IN_X / 2, IN_X / 2, s * y - TL / 2, s * y + TL / 2, PLATE_Z, PLATE_Z + TW)
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


def make_top_frame():
    """Cadre du haut, posé sur les montants : traverses avant et arrière sur toute la
    largeur, au ras de l'extérieur, et traverses latérales entre elles, toutes sur chant."""
    x, y = OUT_X / 2, OUT_Y / 2
    z0, z1 = LEG_H, LEG_H + TL
    long_ = [box(-x, x, s * (y - TW), s * y, z0, z1) for s in (-1, 1)]
    short = [box(s * (x - TW), s * x, -(y - TW), y - TW, z0, z1) for s in (-1, 1)]
    return long_ + short


def assembly(frame_z=HERO_FRAME_Z):
    """Pièces en place, regroupées par type pour les colorer."""
    sides, bars = make_light_frame(frame_z)
    tapes, panels = make_panels(frame_z)
    x0 = IN_X / 2
    return {
        "leg": [make_leg(sx, sy) for sx in (-1, 1) for sy in (-1, 1)],
        "rail": [box(s * (x0 - TW), s * x0, -OUT_Y / 2, OUT_Y / 2, PLATE_Z - TL, PLATE_Z) for s in (-1, 1)]
        + [box(-(x0 - TW), x0 - TW, *BACK_RAIL_Y, PLATE_Z - TL, PLATE_Z)],
        "top": make_top_frame(),
        "slat": make_slats(),
        "reservoir": [make_reservoir()],
        "bac": [make_bac()],
        "frame": sides + bars,
        "pin": make_pins(frame_z),
        "tape": tapes,
        "panel": panels,
    }


CUT_LIST = [
    ("Montant", "tasseau 20 × 40", LEG_H, 4,
     f"{len(FRAME_Z)} trous Ø 8 traversant les 20 mm, au milieu de la face de 40"),
    ("Traverse latérale", "tasseau 20 × 40", OUT_Y, 2, "sur chant, vissée contre l'intérieur des montants"),
    ("Traverse arrière", "tasseau 20 × 40", IN_X - 2 * TW, 1, "sur chant, entre les traverses latérales"),
    ("Latte du porte-bac", "tasseau 20 × 40", IN_X, 4, "à plat, posée sur les traverses latérales"),
    ("Côté du cadre lumière", "tasseau 20 × 40", FRAME_SIDE_L, 2,
     f"sur chant, 2 trous Ø 8 à {FRAME_SIDE_L / 2 - LEG_Y:.0f} mm des bouts"),
    ("Barre du cadre lumière", "tasseau 20 × 40", FRAME_BAR_L, 2, "à plat, posée sur les côtés"),
    ("Traverse haute avant ou arrière", "tasseau 20 × 40", OUT_X, 2, "sur chant, posée sur les montants"),
    ("Traverse haute latérale", "tasseau 20 × 40", OUT_Y - 2 * TW, 2, "sur chant, entre les traverses hautes"),
]


def check():
    """Contrôle les jeux de la conception et affiche les hauteurs utiles."""
    res_x = (-RES[0] / 2, RES[0] / 2)
    res_y = (RES_Y0, RES_Y0 + RES[1])
    rail_in = IN_X / 2 - TW
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
    expect(RES[2] < PLATE_Z - 5, f"réservoir sous le porte-bac : {PLATE_Z - RES[2]:.0f} mm de marge en hauteur")
    expect(res_x[1] < rail_in, f"réservoir entre les traverses latérales : {rail_in - res_x[1]:.1f} mm de chaque côté")
    expect(res_y[1] < BACK_RAIL_Y[0], f"réservoir devant la traverse arrière : {BACK_RAIL_Y[0] - res_y[1]:.0f} mm")
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
    expect(light_top < LEG_H, f"cadre lumière, au plus haut, {LEG_H - light_top:.0f} mm sous le cadre du haut")
    expect(2 * FRAME_SIDE_X[1] < IN_X, f"cadre lumière glissé par l'avant entre les montants : "
           f"{2 * FRAME_SIDE_X[1]:.0f} mm pour {IN_X:.0f} mm de passage")
    print(f"Face LED au-dessus du bord du bac : {low:.0f} à "
          f"{led_face(FRAME_Z[-1]) - BAC_TOP:.0f} mm, {len(FRAME_Z)} positions tous les {HOLE_PITCH:.0f} mm")
    print(f"Trous des montants, axe à {', '.join(f'{leg_hole_z(z):.0f}' for z in FRAME_Z)} mm de la table")
    print(f"Encombrement : {OUT_X:.0f} × {OUT_Y:.0f} × {LEG_H + TL:.0f} mm ; dessous du bac à {BAC_Z:.0f} mm")
    return ok


def print_cut_list():
    print("Liste de débit :")
    for name, mat, length, qty, note in CUT_LIST:
        length = f"{length:.0f}" if isinstance(length, float) else length
        print(f"  {qty} × {name:24s} {mat:20s} {length:>10s} mm  {note}")


def explode(groups):
    shifts = {"leg": (0, 0, 0), "rail": (0, 0, 0), "top": (0, 0, 300), "slat": (0, 0, 70), "reservoir": (0, -320, 0),
              "bac": (0, 0, 170), "frame": (0, 0, 420), "pin": (110, 0, 420), "tape": (0, 0, 370),
              "panel": (0, 0, 320)}
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
    groups = assembly()
    trimesh.util.concatenate([m for ms in groups.values() for m in ms]).export(STL_DIR / "assemblage_v2_vue.stl")
    trimesh.util.concatenate([m for ms in explode(groups).values() for m in ms]).export(
        STL_DIR / "assemblage_v2_eclate_vue.stl")
    print(f"Vues écrites dans {STL_DIR}")


if __name__ == "__main__":
    main()
