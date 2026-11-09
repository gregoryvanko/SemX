#!/usr/bin/env python3
"""Rendus du boîtier de l'électronique et de son couvercle pour le README.

Génère les images dans CAD/images/.
Dépendances : pip install trimesh pyvista pillow scipy
Usage : python CAD/rendu_boitier.py
"""
import numpy as np
import pyvista as pv

from rendu_pieces import UP, add, add_ground, caption, load, new_plotter, save, shot

BOX = "Electronique boitier.stl"
LID = "Electronique couvercle.stl"
COLORS = {"boitier": "#4a7bb0", "couvercle": "#d9d7d1"}
LID_DROP = 50.0          # le STL du couvercle est 50 mm au-dessus de sa position fermée
TARGET = (0, 52.5, 30)


def load_pair(lift=0.0):
    box, lid = load(BOX), load(LID)
    lid.apply_translation((0, 0, lift - LID_DROP))
    return box, lid


def camera(direction, dist, target=TARGET):
    d = np.array(direction, dtype=float)
    t = np.array(target, dtype=float)
    return [tuple(t + d / np.linalg.norm(d) * dist), tuple(t), UP]


def render_scene(lift, direction, dist, labels=(), opacity=1.0, size=(1100, 900), title=None, target=TARGET):
    box, lid = load_pair(lift)
    p = new_plotter(size)
    add_ground(p, z=-1.4)
    add(p, box, COLORS["boitier"])
    if opacity < 1:
        p.add_mesh(pv.wrap(lid), color=COLORS["couvercle"], opacity=opacity, smooth_shading=True)
    else:
        add(p, lid, COLORS["couvercle"])
    if labels:
        p.add_point_labels(np.array([pt for pt, _ in labels], dtype=float), [t for _, t in labels],
                           font_size=22, text_color="#222222", shape=None, show_points=False,
                           always_visible=True, margin=0)
    p.camera_position = camera(direction, dist, target)
    p.camera.view_angle = 24
    if title:
        caption(p, title)
    return shot(p)


def render_views():
    closed = render_scene(0, (-1, 1.3, 0.8), 420, title="Boîtier fermé, côté encoche")
    opened = render_scene(45, (1, -1.3, 1.3), 470, title="Couvercle soulevé", target=(0, 52.5, 45))
    save(np.hstack([closed, opened]), "boitier_vue.png")


def render_top():
    """Vue de dessus, sans couvercle, avec les entretoises et l'encoche repérées."""
    box = load(BOX)
    p = new_plotter((1100, 1100))
    add(p, box, COLORS["boitier"])
    labels = [
        ((-29.8, 0, 36), "33 mm"), ((29.8, 0, 36), "33 mm"),
        ((-29.8, 71.5, 36), "33 mm"), ((29.8, 71.5, 36), "33 mm"),
        ((-24.8, 15, 8), "6 mm"), ((24.8, 60, 8), "6 mm"),
        ((-27.2, 117, 62), "encoche 15 × 10"),
    ]
    p.add_point_labels(np.array([pt for pt, _ in labels], dtype=float), [t for _, t in labels],
                       font_size=24, text_color="#ffffff", shape_color="#222222", shape_opacity=0.6,
                       show_points=False, always_visible=True)
    p.enable_ssao(radius=8, bias=0.5, kernel_size=64)
    p.camera_position = [(0, 20, 400), (0, 60, 0), (0, 1, 0)]
    p.camera.view_angle = 30
    caption(p, "Intérieur, sans couvercle")
    save(shot(p), "boitier_dessus.png")


def render_parts():
    """Les deux pièces dans leur sens d'impression."""
    box = load(BOX)
    box.apply_translation(-box.bounds.mean(axis=0))
    lid = load(LID)
    lid.apply_transform(np.diag([1, 1, -1, 1]))         # retourné : rebord vers le haut
    lid.apply_translation(-lid.bounds.mean(axis=0))
    views = []
    for mesh, key, title in [(box, "boitier", "Boîtier (100 × 125 × 61,4 mm)"),
                             (lid, "couvercle", "Couvercle (100 × 125 × 4,2 mm), à imprimer à l'envers")]:
        p = new_plotter((1100, 800))
        add(p, mesh, COLORS[key])
        d = np.array((1, -1.2, 1.3))
        p.camera_position = [tuple(d / np.linalg.norm(d) * 420), (0, 0, -4), UP]
        p.camera.view_angle = 24
        caption(p, title)
        views.append(shot(p))
    save(np.hstack(views), "boitier_pieces.png")


if __name__ == "__main__":
    render_views()
    render_top()
    render_parts()
