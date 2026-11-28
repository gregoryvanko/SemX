#!/usr/bin/env python3
"""Passe-cloison imprimé : arrivée de l'eau de la pompe par le fond du bac à semis.

Trois pièces :
- le corps : une collerette posée au fond du bac, côté eau, avec une gorge pour un joint
  torique ; dessous, un tube fileté qui traverse le fond, puis un embout cannelé qui
  reçoit le tuyau de la pompe ;
- l'écrou : six pans, vissé sous le bac, il serre le fond entre la collerette et lui ;
- un joint plat, à imprimer en TPU, si l'on n'a pas de joint torique sous la main.

Le filet a des flancs à 45° au lieu des 60° d'un filet métrique : imprimé debout, il ne
présente aucun surplomb de plus de 45° et ne demande pas de support. Le corps s'imprime
la collerette sur le plateau, l'embout vers le haut ; l'écrou et le joint, à plat.

Dépendances : pip install numpy trimesh manifold3d
Usage : python CAD/passe_cloison.py
Écrit dans STL/ les trois pièces, déjà posées dans leur sens d'impression.

Repère de montage : z vers le haut, z = 0 sous la collerette, c'est-à-dire sur le fond
intérieur du bac. Unités : mm.
"""
from pathlib import Path

import numpy as np
import trimesh
from manifold3d import CrossSection, JoinType, Manifold

import cadre_bois as c

ROOT = Path(__file__).resolve().parent.parent
STL_DIR = ROOT / "STL"

# ── Tuyau de la pompe ──────────────────────────────────────────────────────────
TUBE_ID = 6.0                 # diamètre intérieur du tuyau (8 mm extérieur) : à mesurer

# ── Filetage ───────────────────────────────────────────────────────────────────
THREAD_D = 15.5               # diamètre extérieur du filet
PITCH = 3.0                   # pas
DEPTH = 0.9                   # hauteur du filet ; flancs à 45°, le reste du pas en fond et sommet plats
CLEAR = 0.3                   # jeu entre le filet du corps et celui de l'écrou
THREAD_L = 14.0               # longueur filetée sous la collerette
HOLE_D = 16.0                 # trou à percer dans le fond du bac (foret étagé)

# ── Collerette et joint ────────────────────────────────────────────────────────
FLANGE_D = 30.0
FLANGE_T = 4.0
FLANGE_CHAMFER = 1.0
ORING = (18.0, 3.0)           # joint torique : diamètre intérieur × section
GROOVE_W, GROOVE_DEPTH = 4.2, 2.25  # gorge : le joint s'écrase de 25 %
GASKET_T = 1.5                # joint plat en TPU, à la place du joint torique

# ── Écrou ──────────────────────────────────────────────────────────────────────
NUT_AF = 24.0                 # sur plats
NUT_H = 8.0
NUT_CHAMFER = 0.8             # chanfrein d'entrée du taraudage, des deux côtés

# ── Embout cannelé ─────────────────────────────────────────────────────────────
BARB_N = 3
BARB_STEP = 0.7               # saillie d'une cannelure sur le diamètre du tuyau (au rayon)
BARB_L = 4.0                  # longueur d'une cannelure
NECK_L = 3.0                  # entre le filet et la première cannelure
BORE_D = TUBE_ID - 2.4        # passage de l'eau : parois de 1,2 mm sous les cannelures

SEGMENTS = 128
THREAD_SEGMENTS = 72          # points de la section du filet, et tranches par tour : un sommet suit le flanc
PETG_DENSITY = 1.27e-3        # g/mm³
TPU_DENSITY = 1.21e-3

R_MAJ = THREAD_D / 2
R_MIN = R_MAJ - DEPTH
R_SHAFT = TUBE_ID / 2
BARB_TOTAL = NECK_L + BARB_N * BARB_L + 1.0       # avec 1 mm de bout lisse
Z_BOTTOM = -THREAD_L - BARB_TOTAL                 # bout de l'embout


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(mesh.vert_properties[:, :3], mesh.tri_verts, process=True)


def revolve(profile):
    """Solide de révolution autour de z, à partir d'un profil [(r, z), …] fermé."""
    p = np.asarray(profile, float)
    if np.dot(p[:, 0], np.roll(p[:, 1], -1)) - np.dot(np.roll(p[:, 0], -1), p[:, 1]) < 0:
        p = p[::-1]                               # manifold3d ne remplit que les contours dans le sens direct
    return Manifold.revolve(CrossSection([p]), SEGMENTS)


def cylinder(r, z0, z1):
    return Manifold.cylinder(z1 - z0, r, r, SEGMENTS).translate((0, 0, z0))


def thread_section(offset=0.0):
    """Section droite du filet : son rayon suit, en tournant, le profil axial du filet.

    Extrudée avec une torsion d'un tour par pas, elle donne un filet hélicoïdal exact
    (filet à droite, la torsion de manifold3d étant positive dans le sens trigonométrique).
    """
    flat = (PITCH - 2 * DEPTH) / 2                # fond et sommet plats

    def height(u):
        u = u % PITCH
        if u < flat:
            return 0.0
        if u < flat + DEPTH:
            return u - flat
        if u < 2 * flat + DEPTH:
            return DEPTH
        return PITCH - u

    th = np.linspace(0, 2 * np.pi, THREAD_SEGMENTS, endpoint=False)
    r = np.array([R_MIN + height(PITCH * t / (2 * np.pi)) for t in th])
    cs = CrossSection([np.c_[r * np.cos(th), r * np.sin(th)]])
    return cs.offset(offset, JoinType.Round, circular_segments=SEGMENTS) if offset else cs


def threaded(cs, z0, z1):
    turns = (z1 - z0) / PITCH
    return Manifold.extrude(cs, z1 - z0, n_divisions=round(turns * THREAD_SEGMENTS), twist_degrees=360 * turns).translate((0, 0, z0))


def make_body():
    """Corps du passe-cloison, en position de montage."""
    flange = revolve([(0, 0), (FLANGE_D / 2, 0), (FLANGE_D / 2, FLANGE_T - FLANGE_CHAMFER),
                      (FLANGE_D / 2 - FLANGE_CHAMFER, FLANGE_T), (0, FLANGE_T)])
    # Filet, entamé au bas par un chanfrein à 45° pour engager l'écrou.
    lead = R_MAJ - R_MIN + 0.3
    thread = threaded(thread_section(), -THREAD_L, 0.5) ^ revolve(
        [(0, -THREAD_L), (R_MIN - 0.3, -THREAD_L), (R_MAJ, -THREAD_L + lead), (R_MAJ, 0.5), (0, 0.5)])
    # Embout : chaque cannelure s'élargit vers le haut, puis revient au diamètre du tuyau par
    # un épaulement à 45°, qui retient le tuyau et s'imprime sans support, l'embout en haut.
    prof = [(0, -THREAD_L + 0.1), (R_SHAFT, -THREAD_L + 0.1), (R_SHAFT, -THREAD_L - NECK_L)]
    z = -THREAD_L - NECK_L
    for _ in range(BARB_N):
        prof += [(R_SHAFT + BARB_STEP, z - BARB_STEP), (R_SHAFT, z - BARB_L)]
        z -= BARB_L
    prof += [(R_SHAFT, Z_BOTTOM + 0.5), (R_SHAFT - 0.5, Z_BOTTOM), (0, Z_BOTTOM)]
    barb = revolve(prof)
    body = flange + thread + barb
    groove = revolve([(ORING[0] / 2, -1), (ORING[0] / 2 + GROOVE_W, -1),
                      (ORING[0] / 2 + GROOVE_W, GROOVE_DEPTH), (ORING[0] / 2, GROOVE_DEPTH)])
    bore = cylinder(BORE_D / 2, Z_BOTTOM - 1, FLANGE_T + 1) + revolve(
        [(0, FLANGE_T - 1.0), (BORE_D / 2, FLANGE_T - 1.0), (BORE_D / 2 + 1.2, FLANGE_T + 0.2), (0, FLANGE_T + 0.2)])
    return body - groove - bore


def hexagon(af):
    a = np.radians(np.arange(6) * 60 + 30)
    r = af / 2 / np.cos(np.radians(30))
    return CrossSection([np.c_[r * np.cos(a), r * np.sin(a)]])


def make_nut():
    """Écrou, posé à plat de z = 0 à NUT_H, filet commençant à l'angle 0 en z = 0."""
    corner = NUT_AF / 2 / np.cos(np.radians(30))
    c30 = (corner - NUT_AF / 2 * 0.95) * np.tan(np.radians(30))       # chanfrein à 30° des angles, dessus seulement :
    # dessous, posé sur le plateau, il ferait un surplomb dès la première couche
    nut = Manifold.extrude(hexagon(NUT_AF), NUT_H) ^ revolve(
        [(0, -0.1), (corner + 0.1, -0.1), (corner + 0.1, NUT_H - c30 - 0.1),
         (NUT_AF / 2 * 0.95, NUT_H), (0, NUT_H)])
    tap = threaded(thread_section(CLEAR), -PITCH, NUT_H + PITCH)      # un tour entier sous z = 0 : phase 0 en z = 0
    r_in = R_MIN + CLEAR
    sink = revolve([(0, -0.1), (R_MAJ + CLEAR + NUT_CHAMFER, -0.1), (r_in, R_MAJ + CLEAR + NUT_CHAMFER - r_in),
                    (r_in, NUT_H - (R_MAJ + CLEAR + NUT_CHAMFER - r_in)),
                    (R_MAJ + CLEAR + NUT_CHAMFER, NUT_H + 0.1), (0, NUT_H + 0.1)])
    return nut - tap - sink


def make_gasket():
    return cylinder(FLANGE_D / 2 - 1.5, 0, GASKET_T) - cylinder(R_MAJ + 0.4, -1, GASKET_T + 1)


def nut_at(nut, z):
    """Écrou vissé sur le corps, sa face basse en z : la rotation suit le filet."""
    turn = 360 * (z + THREAD_L) / PITCH
    return nut.rotate((0, 0, turn)).translate((0, 0, z))


def check(body, nut, gasket):
    ok = True

    def expect(cond, msg):
        nonlocal ok
        print(("  ok    " if cond else "  ÉCHEC ") + msg)
        ok &= bool(cond)

    print("Contrôles :")
    for name, m in (("corps", body), ("écrou", nut), ("joint", gasket)):
        t = to_trimesh(m)
        expect(t.is_watertight and t.is_volume and m.genus() == 1, f"{name} : maillage fermé, une seule pièce percée")
    # L'écrou se visse : sur toute la course utile, il ne touche pas le corps.
    wall = c.BAC_WALL
    z_tight = -wall - NUT_H                      # écrou serré sous un fond de BAC_WALL
    clash = max((nut_at(nut, z) ^ body).volume() for z in np.linspace(-THREAD_L - 1, z_tight, 9))
    expect(clash < 0.5, f"l'écrou se visse sans toucher le filet du corps (recouvrement max. {clash:.2f} mm³)")
    loose = (nut_at(nut.rotate((0, 0, 180)), z_tight) ^ body).volume()
    expect(loose > 10, "et le filet porte : décalé d'un demi-tour, l'écrou chevaucherait le corps")
    max_wall = THREAD_L - NUT_H - (R_MAJ - R_MIN + 0.3)
    expect(wall <= max_wall - GASKET_T, f"fond du bac de {wall:.0f} mm serré ; le filet accepte jusqu'à "
           f"{max_wall:.1f} mm avec le joint torique, {max_wall - GASKET_T:.1f} mm avec le joint plat")
    expect(THREAD_D < HOLE_D <= ORING[0] - 2, f"trou de Ø {HOLE_D:.0f} : {(HOLE_D - THREAD_D) / 2:.2f} mm autour du filet, "
           f"{(ORING[0] - HOLE_D) / 2:.0f} mm entre le trou et le joint torique")
    squeeze = 1 - GROOVE_DEPTH / ORING[1]
    fill = np.pi * (ORING[1] / 2) ** 2 / (GROOVE_W * GROOVE_DEPTH)
    expect(0.15 <= squeeze <= 0.30 and fill < 0.85, f"joint torique {ORING[0]:.0f} × {ORING[1]:.0f} écrasé de "
           f"{squeeze:.0%}, gorge remplie à {fill:.0%}")
    expect(FLANGE_T - GROOVE_DEPTH >= 1.6, f"{FLANGE_T - GROOVE_DEPTH:.2f} mm de collerette au-dessus de la gorge")
    rim = FLANGE_D / 2 - ORING[0] / 2 - GROOVE_W
    expect(rim >= 1.6, f"{rim:.1f} mm de collerette autour de la gorge")
    corner = NUT_AF / np.cos(np.radians(30))
    expect(corner <= c.DRAIN_D and FLANGE_D <= c.DRAIN_D,
           f"écrou de {corner:.1f} mm sur angles et collerette de Ø {FLANGE_D:.0f} : tournent dans la fente de "
           f"{c.DRAIN_GAP:.0f} mm, dans l'encombrement prévu (Ø {c.DRAIN_D:.0f})")
    expect(BARB_STEP >= 0.5 and (TUBE_ID - BORE_D) / 2 >= 1.2,
           f"embout : cannelures de Ø {TUBE_ID + 2 * BARB_STEP:.1f} dans le tuyau de Ø {TUBE_ID:.0f} intérieur, "
           f"parois de {(TUBE_ID - BORE_D) / 2:.1f} mm, passage de Ø {BORE_D:.1f}")
    below = c.BAC_Z + c.BAC_WALL + Z_BOTTOM - c.RES[2]
    expect(below >= 30, f"bout de l'embout {-Z_BOTTOM - c.BAC_WALL:.0f} mm sous le bac, {below:.0f} mm "
           "au-dessus du réservoir pour courber le tuyau")
    return ok


def print_pose(m, flip=False):
    """Pièce posée sur le plateau ; flip la retourne (collerette du corps en bas)."""
    if flip:
        m = m.rotate((180, 0, 0))
    return m.translate((0, 0, -to_trimesh(m).bounds[0][2]))


def main():
    body, nut, gasket = make_body(), make_nut(), make_gasket()
    ok = check(body, nut, gasket)
    STL_DIR.mkdir(exist_ok=True)
    parts = (("passe_cloison_corps.stl", print_pose(body, flip=True), PETG_DENSITY, "PETG"),
             ("passe_cloison_ecrou.stl", print_pose(nut), PETG_DENSITY, "PETG"),
             ("passe_cloison_joint_tpu.stl", print_pose(gasket), TPU_DENSITY, "TPU"))
    for name, m, rho, mat in parts:
        t = to_trimesh(m)
        out = STL_DIR / name
        t.export(out)
        ext = t.bounds[1] - t.bounds[0]
        print(f"{out.relative_to(ROOT)} : {ext[0]:.1f} × {ext[1]:.1f} × {ext[2]:.1f} mm, "
              f"environ {t.volume * rho:.1f} g de {mat}")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
