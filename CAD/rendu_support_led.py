#!/usr/bin/env python3
"""Rendus 3D du support LED pour le README.

Génère les images dans CAD/images/.
Dépendances : celles de support_led.py, plus pip install pyvista pillow
Usage : python CAD/rendu_support_led.py
"""
from pathlib import Path

import numpy as np
import pyvista as pv
import trimesh
from PIL import Image

import support_led as s

OUT = Path(__file__).resolve().parent / "images"
STL_DIR = s.STL_DIR
UP = (0, 0, 1)
BACKGROUND = "#f4f2ee"

COLORS = {
    "reservoir": "#d9d7d1",
    "bac": "#c9c6be",
    "godet": "#4f4640",
    "base": "#6f8f7a",
    "foot": "#2f6fab",
    "bar": "#9aa3ad",
    "traverse": "#2e9e78",
    "strut": "#8a5fb0",
    "pin": "#d1402f",
    "panel": "#e4e7ea",
    "tape": "#f2a33a",
}

HERO_Z = 273
MIN_Z = 198
MAX_Z = 363
PANEL_DROP = s.TAPE_T + s.PANEL_T


def load_base():
    """Réservoir, bac, godets et capteurs, séparés pour les colorer."""
    res = trimesh.load(STL_DIR / "reservoir_201x201x90_2piliers_paroi2.0.stl", force="mesh")
    bac = trimesh.load(STL_DIR / "bac_semis_201x201x46_socle.stl", force="mesh")
    bac.apply_translation((0, 0, 86))
    bodies = trimesh.load(STL_DIR / "assemblage_v12_vue.stl", force="mesh").split(only_watertight=False)
    godets = [b for b in bodies if len(b.faces) == 984]
    others = [b for b in bodies if len(b.faces) not in (984, 820, 742)]
    return {"reservoir": [res], "bac": [bac], "godet": godets, "base": others}


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


def add_base(plotter, base):
    for key, meshes in base.items():
        for m in meshes:
            add(plotter, m, COLORS[key], edges=key != "godet")


def add_assembly(plotter, parts, base, z_traverse, keep=lambda key, mesh: True):
    add_base(plotter, base)
    for key, meshes in s.assembly(parts, z_traverse).items():
        for m in meshes:
            if keep(key, m):
                add(plotter, m, COLORS[key])


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
    plotter.add_text(text, position=(0.05, 0.93), viewport=True, font_size=16, color="#333333")


def render_hero(parts, base):
    p = new_plotter((2000, 1400))
    add_ground(p)
    add_assembly(p, parts, base, HERO_Z)
    p.enable_ssao(radius=30, bias=1, kernel_size=64)
    p.camera_position = [(760, -1010, 560), (0, 0, 190), UP]
    p.camera.view_angle = 24
    save(shot(p), "support_led_vue.png")


def render_heights(parts, base):
    views = []
    for z in (MIN_Z, MAX_Z):
        p = new_plotter((1200, 1200))
        add_ground(p)
        add_assembly(p, parts, base, z)
        p.enable_ssao(radius=30, bias=1, kernel_size=64)
        p.camera_position = [(850, -1000, 620), (0, 0, 190), UP]
        p.camera.view_angle = 25
        caption(p, f"{z - PANEL_DROP - 130:.0f} mm au-dessus des godets")
        views.append(shot(p))
    save(np.hstack(views), "support_led_hauteurs.png")


def render_exploded(parts, base):
    p = new_plotter((2000, 1700))
    add_ground(p)
    z = 213
    add_base(p, base)
    shifts = {"foot": (110, 0), "bar": (110, 70), "traverse": (110, 300), "strut": (0, 300), "pin": (40, 300),
              "tape": (40, 215), "panel": (0, 170)}
    for key, meshes in s.assembly(parts, z).items():
        dx, dz = shifts[key]
        for m in meshes:
            sign = np.sign(m.centroid[0]) if key not in ("panel", "strut") else 0
            moved = m.copy()
            moved.apply_translation((sign * dx, 0, dz))
            add(p, moved, COLORS[key])

    # Légendes à droite des pièces du côté arrière droit, sur le fond
    x = s.COL_X + 110
    y = s.COL_Y
    labels = [((x, y + 40, 40), "Pied (2)"),
              ((x, y + 25, 300), "Colonne (4)"),
              ((x, s.TRAVERSE_HALF + 15, z + 325), "Traverse (2)"),
              ((s.COL_X + 40, -175, z + 285), "Goupille (4)"),
              ((0, s.COL_Y + 20, z + 345), "Entretoise (2)"),
              ((185, s.TAPE_Y[1] + 50, z + 215), "Adhésif 3M (8)"),
              ((150, s.PANEL_Y[1] + 95, z + 150), "Panneau LED (4)")]
    p.add_point_labels(np.array([pt for pt, _ in labels], dtype=float), [t for _, t in labels],
                       font_size=30, text_color="#222222", shape=None, show_points=False,
                       always_visible=True, margin=0)
    p.enable_ssao(radius=30, bias=1, kernel_size=64)
    p.camera_position = [(1050, -1250, 900), (60, 0, 300), UP]
    p.camera.view_angle = 26
    save(shot(p), "support_led_eclate.png")


def render_slider(parts, base):
    """Gros plan sur un coulisseau et sa goupille, panneaux avant retirés."""
    p = new_plotter((1800, 1300))
    add_ground(p)
    z = 303
    add_assembly(p, parts, base, z, keep=lambda key, m: key not in ("panel", "tape") or m.centroid[1] > 0)
    p.enable_ssao(radius=8, bias=0.5, kernel_size=64)
    focus = (s.COL_X + 8, -s.COL_Y + 25, z + 12)
    p.camera_position = [(focus[0] - 240, focus[1] - 300, focus[2] + 250), focus, UP]
    p.camera.view_angle = 20
    save(shot(p), "support_led_detail_traverse.png")


def render_tape(parts, base):
    """Vue de dessous : plages de collage et adhésifs, panneaux avant retirés."""
    p = new_plotter((1800, 1100))
    add_ground(p, z=-400)
    z = 303
    for key, meshes in s.assembly(parts, z).items():
        for m in meshes:
            if key not in ("foot",) and (key != "panel" or m.centroid[1] > 0):
                add(p, m, COLORS[key])
    p.enable_ssao(radius=8, bias=0.5, kernel_size=64)
    focus = (135, -40, z)
    p.camera_position = [(focus[0] - 330, focus[1] - 360, focus[2] - 300), focus, UP]
    p.camera.view_angle = 26
    save(shot(p), "support_led_detail_collage.png")


def render_foot(parts, base):
    """Gros plan sur le pied collé et l'emboîtement des colonnes."""
    p = new_plotter((1800, 1300))
    add_ground(p)
    add_assembly(p, parts, base, HERO_Z)
    p.enable_ssao(radius=12, bias=0.5, kernel_size=64)
    focus = (s.COL_X, -10, 75)
    p.camera_position = [(focus[0] + 500, focus[1] - 420, focus[2] + 170), focus, UP]
    p.camera.view_angle = 22
    save(shot(p), "support_led_detail_pied.png")


def render_parts(parts):
    items = [("foot", "Pied, 2 pièces", (1, 1.3, 0.65), 2.5), ("bar", "Colonne, 4 pièces", (1, -1, 0.55), 1.8),
             ("traverse", "Traverse, 2 pièces", (-1.3, -1, 0.8), 1.8), ("strut", "Entretoise, 2 pièces", (1, -1, 0.6), 1.8),
             ("pin", "Goupille, 4 pièces", (0.7, -1, 0.9), 2.5)]
    views = []
    for key, title, direction, zoom in items:
        p = new_plotter((1100, 750))
        m = parts[key].copy()
        if key == "strut":
            m.apply_transform(trimesh.transformations.rotation_matrix(np.pi, (1, 0, 0)))
        m.apply_translation(-m.bounds.mean(axis=0))
        add(p, m, COLORS[key])
        d = np.array(direction, dtype=float)
        p.camera_position = [tuple(d / np.linalg.norm(d) * np.linalg.norm(m.extents) * zoom), (0, 0, 0), UP]
        p.camera.view_angle = 24
        caption(p, title)
        views.append(shot(p))
    blank = np.full_like(views[0], views[0][0, 0])
    views.append(blank)
    save(np.vstack((np.hstack(views[:2]), np.hstack(views[2:4]), np.hstack(views[4:]))), "support_led_pieces.png")


def main():
    OUT.mkdir(exist_ok=True)
    parts = s.build_parts()
    base = load_base()
    render_hero(parts, base)
    render_heights(parts, base)
    render_exploded(parts, base)
    render_slider(parts, base)
    render_tape(parts, base)
    render_foot(parts, base)
    render_parts(parts)


if __name__ == "__main__":
    main()
