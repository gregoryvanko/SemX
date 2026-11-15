#!/usr/bin/env python3
"""Rendus 3D du cadre en bois de SemX V2 pour le README.

Génère les images dans CAD/images/.
Dépendances : celles de cadre_bois.py, plus pip install pyvista pillow
Usage : python CAD/rendu_cadre.py
"""
from pathlib import Path

import numpy as np
import pyvista as pv
from PIL import Image

import cadre_bois as c

OUT = Path(__file__).resolve().parent / "images"
UP = (0, 0, 1)
BACKGROUND = "#f4f2ee"

COLORS = {
    "leg": "#c8a272",
    "rail": "#b88f5c",
    "top": "#b88f5c",
    "slat": "#c99e68",
    "reservoir": "#9fc3d6",
    "bac": "#3b3b3b",
    "frame": "#a97c4c",
    "pin": "#d1402f",
    "screw": "#5a5f66",
    "bracket": "#2f6fab",
    "ebox": "#b9bec4",
    "tape": "#f2a33a",
    "panel": "#e4e7ea",
}


def add(plotter, mesh, color, opacity=1.0):
    poly = pv.wrap(mesh)
    plotter.add_mesh(poly, color=color, smooth_shading=True, split_sharp_edges=True, feature_angle=35,
                     ambient=0.28, diffuse=0.72, specular=0.12, specular_power=20, opacity=opacity)
    lines = poly.extract_feature_edges(feature_angle=35, boundary_edges=False,
                                       non_manifold_edges=False, manifold_edges=False)
    if lines.n_cells:
        plotter.add_mesh(lines, color="#2b2b2b", line_width=1, opacity=0.45)


def add_groups(plotter, groups, skip=()):
    for key, meshes in groups.items():
        if key in skip:
            continue
        for m in meshes:
            add(plotter, m, COLORS[key], opacity=0.55 if key == "reservoir" else 1.0)


def new_plotter(size):
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background(BACKGROUND)
    p.add_mesh(pv.Plane(center=(0, 0, -0.6), i_size=4000, j_size=4000), color=BACKGROUND,
               ambient=0.9, diffuse=0.1, specular=0)
    return p


def shot(plotter, name=None):
    plotter.enable_ssao(radius=20, bias=0.5, kernel_size=64)
    plotter.enable_anti_aliasing("ssaa")
    img = plotter.screenshot(return_img=True)
    plotter.close()
    if name:
        Image.fromarray(img).save(OUT / name, optimize=True)
    return img


def caption(plotter, text):
    plotter.add_text(text, position=(0.05, 0.03), viewport=True, font_size=16, color="#333333")


def render_hero():
    p = new_plotter((2000, 1500))
    add_groups(p, c.assembly())
    p.camera_position = [(980, -1480, 960), (0, 0, 330), UP]
    p.camera.view_angle = 26
    shot(p, "cadre_vue.png")


def piece_marks(groups):
    """Repères des pièces en bois (numéros du plan coté), chacun posé sur une pièce visible
    depuis l'avant droit : (numéro, point)."""
    def on(mesh, fx, fy, fz):
        lo, hi = mesh.bounds
        return lo + (hi - lo) * np.array((fx, fy, fz))

    n = c.piece_number
    return [
        (n("Montant"), on(groups["leg"][2], 0.5, 0.0, 0.12)),
        (n("Ceinture basse latérale"), on(groups["rail"][3], 1.0, 0.5, 0.5)),
        (n("Ceinture basse avant ou arrière"), on(groups["rail"][0], 0.3, 0.0, 0.5)),
        (n("Latte du porte-bac"), on(groups["slat"][2], 0.72, 0.0, 1.0)),
        (n("Côté du cadre lumière"), on(groups["frame"][1], 0.5, 0.5, 1.0)),
        (n("Barre du cadre lumière"), on(groups["frame"][2], 0.3, 0.0, 1.0)),
        (n("Ceinture haute avant ou arrière"), on(groups["top"][0], 0.35, 0.0, 0.5)),
        (n("Ceinture haute latérale"), on(groups["top"][3], 1.0, 0.5, 0.5)),
    ]


def add_marks(plotter, marks, size=30):
    plotter.add_point_labels(np.array([pt for _, pt in marks], dtype=float), [f" {k} " for k, _ in marks],
                             font_size=size, bold=True, text_color="white", shape="rounded_rect",
                             shape_color="#222222", shape_opacity=1.0, point_color="#222222", point_size=12,
                             render_points_as_spheres=True, always_visible=True, margin=4)


def render_exploded():
    p = new_plotter((2000, 1700))
    groups = c.explode(c.assembly(c.FRAME_Z[0]))
    add_groups(p, groups)
    add_marks(p, piece_marks(groups))
    caption(p, "Numéros : pièces du plan coté")
    p.camera_position = [(1650, -2050, 1300), (40, -110, 430), UP]
    p.camera.view_angle = 27
    shot(p, "cadre_eclate.png")


def render_heights():
    views = []
    for z in (c.FRAME_Z[0], c.FRAME_Z[-1]):
        p = new_plotter((1200, 1300))
        add_groups(p, c.assembly(z))
        p.camera_position = [(1080, -1380, 760), (0, 0, 320), UP]
        p.camera.view_angle = 27
        caption(p, f"Face LED à {c.led_face(z) - c.BAC_TOP:.0f} mm du bord du bac")
        views.append(shot(p))
    Image.fromarray(np.hstack(views)).save(OUT / "cadre_hauteurs.png", optimize=True)


def render_pin():
    """Gros plan sur un coin du cadre lumière et sa goupille."""
    p = new_plotter((1800, 1300))
    z = 390.0
    add_groups(p, c.assembly(z))
    focus = (c.LEG_X - 10, -c.LEG_Y, z + 10)
    p.camera_position = [(focus[0] + 330, focus[1] - 380, focus[2] + 220), focus, UP]
    p.camera.view_angle = 22
    shot(p, "cadre_detail_goupille.png")


def render_under():
    """Porte-bac et réservoir, vus de l'avant, bac et cadre lumière retirés."""
    p = new_plotter((1800, 1200))
    add_groups(p, c.assembly(), skip=("frame", "pin", "tape", "panel", "bac"))
    p.camera_position = [(380, -1100, 420), (0, 0, 110), UP]
    p.camera.view_angle = 26
    shot(p, "cadre_reservoir.png")


def render_panels():
    """Vue de dessous du cadre lumière : panneaux et adhésifs."""
    p = new_plotter((1800, 1200))
    groups = c.assembly(c.HERO_FRAME_Z)
    for key in ("frame", "tape"):
        for m in groups[key]:
            add(p, m, COLORS[key])
    for m in groups["panel"][:2]:
        add(p, m, COLORS["panel"])
    p.remove_actor(p.renderer.actors[next(iter(p.renderer.actors))])  # sans le sol
    p.camera_position = [(450, -650, c.HERO_FRAME_Z - 480), (0, 0, c.HERO_FRAME_Z + c.TL), UP]
    p.camera.view_angle = 30
    shot(p, "cadre_detail_panneaux.png")


def render_belt():
    """Ceinture du haut : coin assemblé, et ceinture écartée des montants avec ses vis."""
    views = []
    z = c.FRAME_Z[-1]
    groups = c.assembly(z)

    p = new_plotter((1300, 1100))
    add_groups(p, groups, skip=("reservoir", "bac", "slat", "rail"))
    focus = (c.LEG_X, -c.LEG_Y, c.LEG_H - 45)
    p.camera_position = [(focus[0] + 520, focus[1] - 640, focus[2] + 330), focus, UP]
    p.camera.view_angle = 24
    caption(p, "Coin assemblé, cadre lumière au plus haut")
    views.append(shot(p))

    p = new_plotter((1300, 1100))
    for key in ("leg",):
        for m in groups[key]:
            add(p, m, COLORS[key])
    gap = 80.0
    moves = [(0, -gap, 0), (0, gap, 0), (-gap, 0, 0), (gap, 0, 0)]
    for rail, screws, move in zip(c.make_top_frame(), c.make_belt_screws(), moves):
        add(p, rail.copy().apply_translation(move), COLORS["top"])
        for sc in screws:
            add(p, sc.copy().apply_translation(np.array(move)), COLORS["screw"])
    focus = (20, -20, c.LEG_H - 70)
    p.camera_position = [(focus[0] + 760, focus[1] - 940, focus[2] + 600), focus, UP]
    p.camera.view_angle = 30
    caption(p, "Ceinture écartée des montants, avec ses vis")
    views.append(shot(p))
    Image.fromarray(np.hstack(views)).save(OUT / "cadre_detail_ceinture.png", optimize=True)


def render_box():
    """Boîtier de l'électronique au coin arrière droit : en place, puis soulevé hors de sa glissière."""
    views = []
    groups = c.assembly()
    keep = ("leg", "rail", "slat", "reservoir", "bac", "bracket", "top")
    focus = (c.BOX_XC, c.BRK_Y0 + 20, 205)

    for lift, title in ((0.0, "Boîtier glissé dans son support, au coin arrière droit"),
                        (150.0, "Boîtier soulevé : il se glisse par le haut, sans vis")):
        p = new_plotter((1300, 1100))
        for key in keep:
            for m in groups[key]:
                add(p, m, COLORS["rail" if key == "top" else key], opacity=0.55 if key == "reservoir" else 1.0)
        for m in c.make_box(lift):
            add(p, m, COLORS["ebox"])
        p.camera_position = [(focus[0] + 560, focus[1] + 600, focus[2] + 330 + lift / 2),
                             (focus[0], focus[1], focus[2] + lift / 2), UP]
        p.camera.view_angle = 32
        caption(p, title)
        views.append(shot(p))
    Image.fromarray(np.hstack(views)).save(OUT / "cadre_detail_boitier.png", optimize=True)


def render_bracket_part():
    """Support du boîtier seul, dans son sens d'impression (debout)."""
    p = pv.Plotter(off_screen=True, window_size=(1400, 1000))
    p.set_background(BACKGROUND)
    m = c.bracket_print(c.make_bracket())
    m.apply_translation(-m.bounds.mean(axis=0))
    add(p, m, COLORS["bracket"])
    p.camera_position = [(260, 330, 200), (0, 0, 0), UP]
    p.camera.view_angle = 30
    caption(p, "Support du boîtier, debout comme sur le plateau")
    shot(p, "cadre_support_boitier.png")


def render_pin_part():
    """Goupille seule, posée sur son méplat comme sur le plateau d'impression."""
    p = pv.Plotter(off_screen=True, window_size=(1400, 800))
    p.set_background(BACKGROUND)
    m = c.make_pin()
    m.apply_translation(-m.bounds.mean(axis=0))
    add(p, m, COLORS["pin"])
    p.camera_position = [(-38, -60, 48), (0, 0, 0), UP]
    p.camera.view_angle = 30
    shot(p, "cadre_goupille.png")


def main():
    OUT.mkdir(exist_ok=True)
    render_pin_part()
    render_bracket_part()
    render_box()
    render_belt()
    render_hero()
    render_exploded()
    render_heights()
    render_pin()
    render_under()
    render_panels()


if __name__ == "__main__":
    main()
