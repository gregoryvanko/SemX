#!/usr/bin/env python3
"""Rendus des pièces de la chambre de culture (hors support LED) pour le README.

Génère les images dans CAD/images/.
Dépendances : pip install trimesh pyvista pillow scipy
Usage : python CAD/rendu_pieces.py
"""
from pathlib import Path

import numpy as np
import pyvista as pv
import trimesh
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
STL_DIR = ROOT / "STL"
OUT = Path(__file__).resolve().parent / "images"
UP = (0, 0, 1)
BACKGROUND = "#f4f2ee"

COLORS = {
    "reservoir": "#d9d7d1",
    "bac": "#c9c6be",
    "godet": "#4f4640",
    "mesure": "#6f8f7a",
    "couvercle": "#2f6fab",
    "support": "#2e9e78",
    "tuyau": "#d1402f",
    "capteur": "#8a5fb0",
    "sonde": "#9aa3ad",
    "grille": "#e0a030",
}

# (fichier, clé de couleur, titre, direction de la caméra, recul)
PARTS = [
    ("reservoir_201x201x90_2piliers_paroi2.0.stl", "reservoir", "Réservoir", (1, -1.2, 1.1), 2.3),
    ("bac_semis_201x201x46_socle.stl", "bac", "Bac de semis", (1, -1.2, 1.1), 2.3),
    ("godet_semis_36x36x42.stl", "godet", "Godet de semis", (1, -1.2, 1.0), 2.5),
    ("godet_mesure_36x19x42.stl", "mesure", "Godet de mesure", (1, -1.2, 1.0), 2.5),
    ("couvercle_godet_mesure_36x19.stl", "couvercle", "Couvercle du godet de mesure", (1, -1.2, 1.3), 2.4),
    ("support_godet_mesure_36x19.stl", "support", "Support du godet de mesure", (1, -1.2, 1.1), 2.4),
    ("Tuyau Pompe.stl", "tuyau", "Tuyau de pompe", (1, -1.2, 1.0), 2.8),
    ("grille_godets_pieds_193x193x2.stl", "grille", "Grille sur pieds des godets", (1, -1.2, 1.6), 1.9),
    ("grille_godets_pied_14x33.stl", "grille", "Pied de la grille (x 8)", (1, -1.2, 1.0), 2.6),
]


def load(name):
    return trimesh.load(STL_DIR / name, force="mesh")


def add(plotter, mesh, color, edges=True):
    poly = pv.wrap(mesh)
    plotter.add_mesh(poly, color=color, smooth_shading=True, split_sharp_edges=True, feature_angle=35,
                     ambient=0.28, diffuse=0.72, specular=0.12, specular_power=20)
    if edges:
        lines = poly.extract_feature_edges(feature_angle=35, boundary_edges=False,
                                           non_manifold_edges=False, manifold_edges=False)
        if lines.n_cells:
            plotter.add_mesh(lines, color="#2b2b2b", line_width=1, opacity=0.45)


def add_ground(plotter, z=-0.6):
    plotter.add_mesh(pv.Plane(center=(0, 0, z), i_size=3000, j_size=3000), color=BACKGROUND,
                     ambient=0.9, diffuse=0.1, specular=0)


def new_plotter(size):
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background(BACKGROUND)
    return p


def shot(plotter):
    plotter.enable_anti_aliasing("ssaa")
    img = plotter.screenshot(return_img=True)
    plotter.close()
    return img


def save(img, name):
    Image.fromarray(img).save(OUT / name, optimize=True)


def caption(plotter, text):
    plotter.add_text(text, position=(0.05, 0.92), viewport=True, font_size=16, color="#333333")


def classify(body):
    """Corps de l'assemblage, reconnus par leurs dimensions."""
    ext = tuple(np.round(body.extents))
    if ext[:2] == (201, 201):
        return "reservoir" if ext[2] == 90 else "bac"
    if ext == (36, 36, 42):
        return "godet"
    if ext == (36, 19, 42):
        return "mesure"
    if ext[:2] == (36, 19):
        return "couvercle"
    if ext[0] == 23:
        return "capteur"
    return "sonde"


def render_assembly(name, out, camera, labels=()):
    p = new_plotter((2000, 1500))
    add_ground(p)
    for body in load(name).split(only_watertight=False):
        key = classify(body)
        add(p, body, COLORS[key], edges=key != "godet")
    if labels:
        p.add_point_labels(np.array([pt for pt, _ in labels], dtype=float), [t for _, t in labels],
                           font_size=30, text_color="#222222", shape=None, show_points=False,
                           always_visible=True, margin=0)
    p.enable_ssao(radius=30, bias=1, kernel_size=64)
    p.camera_position = camera
    p.camera.view_angle = 24
    save(shot(p), out)


def render_part(name, key, title, direction, zoom, size=(1100, 800)):
    p = new_plotter(size)
    m = load(name)
    m.apply_translation(-m.bounds.mean(axis=0))
    add(p, m, COLORS[key])
    d = np.array(direction, dtype=float)
    p.camera_position = [tuple(d / np.linalg.norm(d) * np.linalg.norm(m.extents) * zoom), (0, 0, 0), UP]
    p.camera.view_angle = 24
    caption(p, title)
    return shot(p)


def render_parts():
    views = [render_part(*item) for item in PARTS]
    if len(views) % 2:
        views.append(np.full_like(views[0], views[0][0, 0]))
    rows = [np.hstack(views[i:i + 2]) for i in range(0, len(views), 2)]
    save(np.vstack(rows), "pieces.png")


def render_grid():
    """Bac, godets, godet de mesure et grille sur pieds, montés puis éclatés."""
    import grille_godets_pieds as gp
    grid, *feet = gp.make_assembly()
    godet = load("godet_semis_36x36x42.stl")
    mesure = load("godet_mesure_36x19x42.stl")
    lid = load("couvercle_godet_mesure_36x19.stl")
    lid.apply_transform(np.diag([1, -1, -1, 1]))           # emboîté, dessus vers le haut
    mx, my = gp.MESURE_XY[0] - 1.0, gp.MESURE_XY[1]
    lid.apply_translation((mx, my, 46.0 - lid.bounds[1, 2]))
    cells = ((-78, -78), (-39, 0), (0, -39), (39, 39), (78, 39), (39, 78))
    views = (("grille_pieds_vue.png", 0, 0, True),
             ("grille_pieds_eclate.png", 70, 35, False))
    for name, lift_grid, lift_feet, with_godets in views:
        p = new_plotter((2000, 1500))
        add_ground(p)
        add(p, load("bac_semis_201x201x46_socle.stl"), COLORS["bac"])
        if with_godets:
            for x, y in cells:
                add(p, godet.copy().apply_translation((x, y, 2)), COLORS["godet"], edges=False)
        add(p, mesure.copy().apply_translation((mx, my, 2)), COLORS["mesure"])
        add(p, lid, COLORS["couvercle"])
        add(p, grid.copy().apply_translation((0, 0, lift_grid)), COLORS["grille"])
        for f in feet:
            add(p, f.copy().apply_translation((0, 0, lift_feet)), COLORS["grille"])
        p.enable_ssao(radius=30, bias=1, kernel_size=64)
        p.camera_position = [(330, -420, 440 + lift_grid), (0, 0, 20 + lift_grid / 2), UP]
        p.camera.view_angle = 24
        save(shot(p), name)


def main():
    OUT.mkdir(exist_ok=True)
    render_assembly("assemblage_v12_vue.stl", "assemblage_vue.png",
                    [(520, -640, 470), (0, 0, 80), UP])
    render_assembly("assemblage_v12_eclate_vue.stl", "assemblage_eclate.png",
                    [(640, -790, 560), (0, 0, 205), UP])
    render_parts()
    render_grid()


if __name__ == "__main__":
    main()
