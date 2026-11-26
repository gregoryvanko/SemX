#!/usr/bin/env python3
"""Attache pour tenir côte à côte deux tuyaux souples de Ø 8 mm extérieur.

Deux pinces en C, accolées et parallèles, ouvertes du même côté : on y clipse les deux
tuyaux par le dessus. L'ouverture, plus étroite que le tuyau, le retient une fois en
place, et l'alésage le serre légèrement pour que l'attache ne glisse pas le long.

La pièce s'imprime à plat, le profil en C sur le plateau et les tuyaux à la verticale :
les pinces fléchissent dans le plan des couches, ce qui les rend souples sans casser,
et aucun support n'est nécessaire.

Dépendances : pip install numpy trimesh shapely
Usage : python CAD/attache_tuyaux.py
Écrit STL/attache_tuyaux_8mm.stl, déjà posé sur le plateau dans son sens d'impression.
Unités : mm.
"""
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Point, box

ROOT = Path(__file__).resolve().parent.parent
STL_DIR = ROOT / "STL"

# ── Tuyau ──────────────────────────────────────────────────────────────────────
TUBE_OD = 8.0                 # diamètre extérieur des tuyaux souples

# ── Attache ────────────────────────────────────────────────────────────────────
GRIP_D = 7.8                  # alésage des pinces : serre légèrement le tuyau
WALL = 1.8                    # épaisseur des pinces
WEB = 1.8                     # paroi entre les deux tuyaux
OPENING = 6.0                 # largeur de l'ouverture, plus petite que le tuyau
LENGTH = 12.0                 # longueur de l'attache le long des tuyaux
ROUND = 0.4                   # arrondi des arêtes du profil
SEGMENTS = 96                 # facettes sur un tour

PITCH = GRIP_D + WEB          # entraxe des deux tuyaux
R_IN, R_OUT = GRIP_D / 2, GRIP_D / 2 + WALL


def profile():
    """Profil en deux C accolés, ouvertures vers +y, centré sur l'origine."""
    res = SEGMENTS // 4
    centers = [(-PITCH / 2, 0.0), (PITCH / 2, 0.0)]
    body = Point(centers[0]).buffer(R_OUT, res).union(Point(centers[1]).buffer(R_OUT, res))
    body = body.union(box(-PITCH / 2, -R_OUT, PITCH / 2, 0.0))       # dos plein entre les pinces
    for cx, cy in centers:
        body = body.difference(Point(cx, cy).buffer(R_IN, res))
        body = body.difference(box(cx - OPENING / 2, cy, cx + OPENING / 2, cy + R_OUT + 1))
    return body.buffer(-ROUND, res).buffer(ROUND, res)               # arrondit les angles vifs


def make_clip():
    mesh = trimesh.creation.extrude_polygon(profile(), LENGTH)
    mesh.apply_translation(-mesh.bounds[0] * [1, 1, 0] - [(mesh.bounds[1][0] - mesh.bounds[0][0]) / 2,
                                                         (mesh.bounds[1][1] - mesh.bounds[0][1]) / 2, 0])
    return mesh


def check(mesh, poly):
    ok = True

    def expect(cond, msg):
        nonlocal ok
        print(("  ok    " if cond else "  ÉCHEC ") + msg)
        ok &= bool(cond)

    print("Contrôles :")
    expect(mesh.is_watertight and mesh.is_volume, "maillage fermé et orienté")
    expect(poly.geom_type == "Polygon", "profil d'un seul tenant")
    expect(GRIP_D < TUBE_OD, f"tuyau serré de {(TUBE_OD - GRIP_D) / 2:.1f} mm par côté dans la pince")
    expect(0.65 * TUBE_OD <= OPENING < TUBE_OD - 1,
           f"ouverture de {OPENING:.1f} mm : le tuyau s'y écrase de {TUBE_OD - OPENING:.1f} mm pour entrer, puis reste tenu")
    expect(WALL >= 1.2 and WEB >= 1.2, f"parois de {WALL:.1f} mm et cloison de {WEB:.1f} mm, ≥ 3 lignes de 0,4 mm")
    # Le tuyau doit dépasser la moitié de la pince pour être retenu : l'ouverture se trouve au-dessus du centre.
    tip = np.sqrt(R_IN ** 2 - (OPENING / 2) ** 2)
    expect(tip > 1.5, f"becs de la pince {tip:.1f} mm au-dessus de l'axe du tuyau")
    return ok


def main():
    poly = profile()
    mesh = make_clip()
    ok = check(mesh, poly)
    STL_DIR.mkdir(exist_ok=True)
    out = STL_DIR / "attache_tuyaux_8mm.stl"
    mesh.export(out)
    ext = mesh.bounds[1] - mesh.bounds[0]
    print(f"{out.relative_to(ROOT)} : {ext[0]:.1f} × {ext[1]:.1f} × {ext[2]:.1f} mm, entraxe des tuyaux {PITCH:.1f} mm, "
          f"environ {mesh.volume / 1000 * 1.27:.1f} g de PETG en plein")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
