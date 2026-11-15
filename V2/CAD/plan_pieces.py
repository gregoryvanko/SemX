#!/usr/bin/env python3
"""Plan coté des pièces en bois de SemX V2.

Chaque pièce est dessinée à plat, vue sur sa face de 40 mm, avec sa longueur, ses
perçages, l'emplacement des pièces qui s'y fixent et les vis. Les cotes viennent de
cadre_bois.py : le plan suit toute modification du modèle.

Dépendances : celles de cadre_bois.py, plus pip install matplotlib
Usage : python CAD/plan_pieces.py
Écrit CAD/images/cadre_pieces_cotes.png et plan_pieces_bois.pdf (à imprimer).
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

import cadre_bois as c

HERE = Path(__file__).resolve().parent
PNG = HERE / "images" / "cadre_pieces_cotes.png"
PDF = HERE.parent / "plan_pieces_bois.pdf"

WOOD = "#e9d3ad"
EDGE = "#6b4a22"
ZONE = "#b9d3e8"
ZONE_ALT = "#f4c99a"
REST = "#3f9b5a"      # pièce posée sur le dessus
INK = "#222222"
DIM = "#2f5f8f"
H = c.TL          # hauteur dessinée : face de 40 mm
ROW = 150.0       # pas vertical entre deux pièces
X0 = 0.0
FS = 7.5


def dim_h(ax, x0, x1, y, text, above=True):
    """Cote horizontale entre x0 et x1, à la hauteur y."""
    ax.annotate("", (x0, y), (x1, y), arrowprops=dict(arrowstyle="<->", color=DIM, lw=0.7, shrinkA=0, shrinkB=0))
    ax.text((x0 + x1) / 2, y + (2.5 if above else -2.5), text, ha="center", va="bottom" if above else "top",
            fontsize=FS, color=DIM)


def ext(ax, x, y0, y1):
    ax.plot([x, x], [y0, y1], color=DIM, lw=0.4)


def piece(ax, y, length, title, qty, note):
    ax.add_patch(Rectangle((X0, y), length, H, facecolor=WOOD, edgecolor=EDGE, lw=1.0, zorder=1))
    num = c.piece_number(title)
    ax.add_patch(Circle((X0 + 7, y + H + 38), 8, facecolor=INK, edgecolor=INK))
    ax.text(X0 + 7, y + H + 37.5, str(num), fontsize=9, fontweight="bold", color="white", ha="center", va="center")
    ax.text(X0 + 20, y + H + 33, f"{title} — {qty} pièce{'s' if qty > 1 else ''}", fontsize=10, fontweight="bold",
            color=INK, va="bottom")
    ax.text(X0, y + H + 24, note, fontsize=FS, color="#555555", va="bottom")
    ext(ax, X0, y + H, y + H + 16)
    ext(ax, X0 + length, y + H, y + H + 16)
    dim_h(ax, X0, X0 + length, y + H + 12, f"{length:.0f}")
    # section, à droite
    sx = X0 + length + 25
    ax.add_patch(Rectangle((sx, y), c.TW, H, facecolor=WOOD, edgecolor=EDGE, lw=0.8, hatch="////"))
    ax.text(sx + c.TW + 5, y + H / 2, "section\n20 × 40", fontsize=FS - 1, va="center", color="#555555")


def rest(ax, y, x0, x1, num):
    """Pièce n° num posée sur le dessus : bande verte le long de l'arête du haut, numéro au-dessus."""
    ax.add_patch(Rectangle((X0 + x0, y + H - 7), x1 - x0, 7, facecolor=REST, edgecolor="#1f5e33", lw=0.6,
                           alpha=0.85, zorder=3))
    ax.text(X0 + (x0 + x1) / 2, y + H + 1.5, str(num), fontsize=FS, fontweight="bold", color="#1f5e33",
            ha="center", va="bottom", zorder=4)


def zone(ax, y, x0, x1, label, color=ZONE, band=None):
    """Emplacement d'une pièce fixée sur celle-ci, hachuré. Avec band, seulement une bande
    de cette épaisseur le long de l'arête du haut (pièce posée dessus)."""
    h = H if band is None else band
    y0 = y if band is None else y + H - band
    ax.add_patch(Rectangle((X0 + x0, y0), x1 - x0, h, facecolor=color, edgecolor=DIM, lw=0.5, alpha=0.55,
                           hatch="\\\\\\", zorder=2))
    if label:
        ax.text(X0 + (x0 + x1) / 2, y + H / 2, label, fontsize=FS - 1.5, ha="center", va="center", color=INK,
                zorder=4, rotation=90 if x1 - x0 < 30 else 0)


def holes(ax, y, xs, zc=None):
    zc = y + H / 2 if zc is None else zc
    for x in xs:
        ax.add_patch(Circle((X0 + x, zc), c.HOLE_D / 2, facecolor="white", edgecolor=INK, lw=0.8, zorder=5))


def screws(ax, y, xs, zs=(H / 2 - 10, H / 2 + 10)):
    for x in xs:
        for z in zs:
            ax.plot(X0 + x, y + z, marker="x", ms=3.5, mew=0.9, color="#8a1c1c", zorder=6)


def fmt(v):
    return f"{v:g}".replace(".", ",")


def chain(ax, y, xs, length, below=8.0):
    """Cotes cumulées depuis le bout gauche, sous la pièce."""
    yy = y - below
    for i, x in enumerate(sorted(set(xs))):
        k = i % 3
        ext(ax, X0 + x, y, yy - 3 - 7 * k)
        ax.text(X0 + x, yy - 4 - 7 * k, fmt(x), fontsize=FS - 1, ha="center", va="top", color=DIM)
    ext(ax, X0, y, yy - 3)
    ax.text(X0, yy - 4, "0", fontsize=FS - 1, ha="center", va="top", color=DIM)


def legend(ax, y):
    """Légende graphique : un échantillon de chaque symbole du plan."""
    x = X0
    fs = FS + 0.5

    def label(text):
        nonlocal x
        t = ax.text(x, y, text, fontsize=fs, color="#333333", va="center")
        x += 6.2 * len(text) * fs / 8 + 18

    ax.add_patch(Circle((x + 6, y), 6, facecolor=INK))
    ax.text(x + 6, y, "n", fontsize=fs, color="white", ha="center", va="center", fontweight="bold")
    x += 16
    label("repère de la pièce sur les vues de montage")
    for col in (ZONE, ZONE_ALT):
        ax.add_patch(Rectangle((x, y - 7), 12, 14, facecolor=col, edgecolor=DIM, lw=0.5, alpha=0.55, hatch="\\\\\\"))
        x += 15
    label("pièce vissée contre cette face (nom écrit dessus)")
    x, y = X0, y - 24
    ax.add_patch(Rectangle((x, y + 1), 22, 6, facecolor=REST, edgecolor="#1f5e33", lw=0.6, alpha=0.85))
    ax.add_patch(Rectangle((x, y - 7), 22, 8, facecolor=WOOD, edgecolor=EDGE, lw=0.6))
    ax.text(x + 11, y + 8, "n", fontsize=fs - 1, color="#1f5e33", fontweight="bold", ha="center", va="bottom")
    x += 27
    label("pièce n posée sur le dessus")
    ax.plot(x + 4, y, marker="x", ms=4, mew=1, color="#8a1c1c")
    x += 11
    label("vis 4 × 40 mm")
    ax.add_patch(Circle((x + 4, y), c.HOLE_D / 2, facecolor="white", edgecolor=INK, lw=0.8))
    x += 12
    label("trou Ø 8 traversant")


def main():
    lx = c.IN_X / 2
    rows = []

    # ── Montant ──
    leg_holes = [c.leg_hole_z(z) for z in c.FRAME_Z]
    rail = (c.PLATE_Z - c.TL, c.PLATE_Z)
    belt = (c.LEG_H - c.TL, c.LEG_H)
    rows.append(("Montant", 4, c.LEG_H,
                 "Vu sur la face de 40 mm, bas à gauche. Trous Ø 8 traversant les 20 mm, au milieu de la face.",
                 lambda ax, y: (zone(ax, y, *rail, "traverse\nlatérale\n(face int.)"),
                                zone(ax, y, *belt, "ceinture\n(face ext.)", ZONE_ALT),
                                holes(ax, y, leg_holes),
                                chain(ax, y, [rail[0], rail[1]] + leg_holes + [belt[0]], c.LEG_H))))

    # ── Traverse latérale (sous le porte-bac) ──
    L = c.OUT_Y
    slats = sorted(L / 2 + s * yc + d for yc in c.SLAT_Y for s in (-1, 1) for d in (-c.TL / 2,))
    back = (L / 2 + c.BACK_RAIL_Y[0], L / 2 + c.BACK_RAIL_Y[1])
    rows.append(("Traverse latérale", 2, L,
                 "Sur chant, contre l'intérieur des montants, dessus à 150 mm du sol. Avant à gauche. "
                 "Lattes posées dessus, traverse arrière vissée contre.",
                 lambda ax, y, L=L, slats=slats, back=back: (zone(ax, y, 0, c.TL, "montant"), zone(ax, y, L - c.TL, L, "montant"),
                                [rest(ax, y, s0, s0 + c.TL, c.piece_number("Latte du porte-bac")) for s0 in slats],
                                zone(ax, y, *back, "trav.\narr.", ZONE_ALT),
                                screws(ax, y, [c.TL / 2, L - c.TL / 2]),
                                chain(ax, y, [c.TL] + [v for s0 in slats for v in (s0, s0 + c.TL)] + list(back)
                                      + [L - c.TL], L))))

    # ── Traverse arrière ──
    L = c.IN_X - 2 * c.TW
    rows.append(("Traverse arrière", 1, L,
                 "Sur chant, entre les traverses latérales, au ras de leur dessus, vissée à travers elles.",
                 lambda ax, y: None))

    # ── Latte du porte-bac ──
    L = c.IN_X
    rows.append(("Latte du porte-bac", 4, L,
                 "Posée à plat (face de 40 dessus) sur les traverses latérales. Axes à ±40 et ±84,5 mm du milieu "
                 "du bac : fente de 40 mm au centre pour le trop-plein.",
                 lambda ax, y, L=L: (zone(ax, y, 0, c.TW, "trav."), zone(ax, y, L - c.TW, L, "trav."),
                                screws(ax, y, [c.TW / 2, L - c.TW / 2], zs=(H / 2,)),
                                chain(ax, y, [c.TW, L - c.TW], L))))

    # ── Côté du cadre lumière ──
    L = c.FRAME_SIDE_L
    side_holes = [L / 2 - c.LEG_Y, L / 2 + c.LEG_Y]
    rows.append(("Côté du cadre lumière", 2, L,
                 "Sur chant. Trous Ø 8 traversant les 20 mm, à mi-hauteur, pour les goupilles. "
                 "Barres posées dessus, au ras des bouts.",
                 lambda ax, y, L=L, side_holes=side_holes: (rest(ax, y, 0, c.TL, c.piece_number("Barre du cadre lumière")), rest(ax, y, L - c.TL, L, c.piece_number("Barre du cadre lumière")),
                                holes(ax, y, side_holes),
                                chain(ax, y, [c.TL] + side_holes + [L - c.TL], L))))

    # ── Barre du cadre lumière ──
    L = c.FRAME_BAR_L
    rows.append(("Barre du cadre lumière", 2, L,
                 "À plat sur les côtés, au ras de leurs bouts. 2 vis par croisement, de haut en bas. "
                 "Panneaux LED collés dessous.",
                 lambda ax, y, L=L: (zone(ax, y, 0, c.TW, "côté"), zone(ax, y, L - c.TW, L, "côté"),
                                screws(ax, y, [c.TW / 2, L - c.TW / 2]),
                                chain(ax, y, [c.TW, L - c.TW], L))))

    # ── Ceinture avant ou arrière ──
    L = c.OUT_X + 2 * c.TW
    rows.append(("Ceinture avant ou arrière", 2, L,
                 "Sur chant, contre les faces de 20 mm des montants, dessus au ras du haut. "
                 "Couvre les bouts des ceintures latérales.",
                 lambda ax, y, L=L: (zone(ax, y, 0, c.TW, "ceint.\nlat.", ZONE_ALT), zone(ax, y, L - c.TW, L, "ceint.\nlat.", ZONE_ALT),
                                zone(ax, y, c.TW, 2 * c.TW, "mont."), zone(ax, y, L - 2 * c.TW, L - c.TW, "mont."),
                                screws(ax, y, [c.TW / 2, 1.5 * c.TW, L - 1.5 * c.TW, L - c.TW / 2]),
                                chain(ax, y, [c.TW, 2 * c.TW, L - 2 * c.TW, L - c.TW], L))))

    # ── Ceinture latérale ──
    L = c.OUT_Y
    rows.append(("Ceinture latérale", 2, L,
                 "Sur chant, contre les faces de 40 mm des montants, dessus au ras du haut, bouts au ras des montants.",
                 lambda ax, y, L=L: (zone(ax, y, 0, c.TL, "montant"), zone(ax, y, L - c.TL, L, "montant"),
                                screws(ax, y, [c.TL / 2, L - c.TL / 2]),
                                chain(ax, y, [c.TL, L - c.TL], L))))

    n = len(rows)
    width = c.LEG_H + 110
    fig_h = (n * ROW + 90) / 25.4 * 0.55
    fig, ax = plt.subplots(figsize=(width / 25.4 * 0.55, fig_h))
    for i, (title, qty, length, note, extra) in enumerate(rows):
        y = (n - 1 - i) * ROW
        piece(ax, y, length, title, qty, note)
        extra(ax, y)

    total = sum(q * l for _, m, l, q, _ in c.CUT_LIST if m.startswith("tasseau"))
    ax.text(X0, n * ROW + 20, "SemX V2 — pièces en bois (tasseau raboté 20 × 40 mm), cotes en mm",
            fontsize=13, fontweight="bold", color=INK)
    ax.text(X0, n * ROW + 4, f"Total : {total / 1000:.2f} m de tasseau. Cotes depuis le bout gauche de chaque pièce.",
            fontsize=FS + 0.5, color="#444444")
    legend(ax, n * ROW - 12)
    ax.set_xlim(-10, width)
    ax.set_ylim(-40, n * ROW + 40)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    PNG.parent.mkdir(exist_ok=True)
    fig.savefig(PNG, dpi=220, facecolor="white")
    fig.savefig(PDF, facecolor="white")
    print(f"Plan écrit : {PNG} et {PDF}")


if __name__ == "__main__":
    main()
