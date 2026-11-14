#!/usr/bin/env python3
"""Vues d'assemblage de SemiX : réservoir, bac, grille sur pieds, godets et capteurs.

Le bac porte 24 godets de semis et, dans la case d'angle du trop-plein, le godet de
mesure en L. Le capteur d'humidité capacitif et la sonde DS18B20 du semis, représentés
par de simples volumes, sont plantés directement dans le terreau du godet de mesure,
un dans chaque branche du L.

Dépendances : pip install numpy scipy trimesh manifold3d shapely mapbox_earcut
Usage : python CAD/assemblage.py
Écrit STL/assemblage_v13_vue.stl et STL/assemblage_v13_eclate_vue.stl, non destinés à
l'impression. Unités : mm.
"""
from pathlib import Path

import numpy as np
import trimesh

import grille_godets_pieds as gp

ROOT = Path(__file__).resolve().parent.parent
STL_DIR = ROOT / "STL"

BAC_Z = 86.0              # le socle du bac s'emboîte de 4 mm dans le réservoir
PITCH = 39.0
MESURE_CELL = (78.0, 78.0)
GODET_FLOOR = 5.2         # fond intérieur du godet, au-dessus du dessous des pieds

# Capteurs, dans le repère du godet de mesure (branches du L : y < 3 et x < 3)
CAPTEUR = (1.6, 23.0, 98.0)       # lame du capteur capacitif, électronique comprise
CAPTEUR_XY = (-7.5, 0.0)          # dans la branche le long de y, le long de la face -x
CAPTEUR_GAP = 1.0                 # au-dessus du fond
SONDE_D, SONDE_L = 6.0, 60.0      # sonde DS18B20
SONDE_XY = (9.0, -6.0)            # au bout de la branche le long de x
SONDE_GAP = 3.0

# Décalages verticaux de la vue éclatée
EXPLODE = {"reservoir": 0, "bac": 45, "grille": 95, "godet": 150, "mesure": 150, "capteur": 200,
           "sonde": 200}


def load(name):
    return trimesh.load(STL_DIR / name, force="mesh")


def sensors():
    x, y = MESURE_CELL
    floor = BAC_Z + 2 + GODET_FLOOR
    blade = trimesh.creation.box(extents=CAPTEUR)
    blade.apply_translation((x + CAPTEUR_XY[0], y + CAPTEUR_XY[1], floor + CAPTEUR_GAP + CAPTEUR[2] / 2))
    probe = trimesh.creation.cylinder(radius=SONDE_D / 2, height=SONDE_L, sections=32)
    probe.apply_translation((x + SONDE_XY[0], y + SONDE_XY[1], floor + SONDE_GAP + SONDE_L / 2))
    return blade, probe


def make_assembly(exploded=False):
    """Liste de (clé, maillage) en place, ou éclatés suivant z."""
    parts = [("reservoir", load("reservoir_201x201x90_2piliers_paroi2.0.stl"))]
    bac = load("bac_semis_201x201x46_socle.stl").apply_translation((0, 0, BAC_Z))
    parts.append(("bac", bac))
    for m in gp.make_assembly():
        parts.append(("grille", m.apply_translation((0, 0, BAC_Z))))
    godet = load("godet_semis_36x36x42.stl")
    cells = (np.arange(5) - 2) * PITCH
    for x in cells:
        for y in cells:
            if (x, y) != MESURE_CELL:
                parts.append(("godet", godet.copy().apply_translation((x, y, BAC_Z + 2))))
    mesure = load("godet_mesure_L_36x36x42.stl")
    parts.append(("mesure", mesure.apply_translation((*MESURE_CELL, BAC_Z + 2))))
    blade, probe = sensors()
    parts += [("capteur", blade), ("sonde", probe)]
    if exploded:
        for key, m in parts:
            m.apply_translation((0, 0, EXPLODE[key]))
    return parts


def main():
    for exploded, name in ((False, "assemblage_v13_vue.stl"), (True, "assemblage_v13_eclate_vue.stl")):
        parts = make_assembly(exploded)
        m = trimesh.util.concatenate([p for _, p in parts])
        m.export(STL_DIR / name)
        print(f"{name} : {len(parts)} pièces, {m.extents[2]:.1f} mm de haut")
    # Les capteurs ne touchent pas les parois du godet de mesure
    mesure = dict(make_assembly())["mesure"]
    for s in sensors():
        assert trimesh.boolean.intersection([mesure, s], engine="manifold").volume < 1e-6


if __name__ == "__main__":
    main()
