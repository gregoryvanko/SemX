#!/usr/bin/env python3
"""Circuit imprimé simple face de SemiX, à graver à la CNC.

Relie l'ESP32 AZ-Delivery DevKit C V4 (38 broches) aux deux sondes DS18B20,
au capteur d'humidité du sol, aux deux relais et à un bornier d'alimentation 5 V.

Génère dans PCB/fabrication/ :
  gerber/  : cuivre (face dessous), contour et perçage, pour FlatCAM, KiCad, etc.
  gcode/   : G-code GRBL prêt à l'emploi (isolation, perçage, découpe), vu côté cuivre
et dans PCB/images/ : plan d'implantation et aperçu de l'usinage.

Dépendances : pip install shapely matplotlib
Usage : python PCB/pcb_semix.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import substring, unary_union

HERE = Path(__file__).resolve().parent
OUT = HERE / "fabrication"
IMG = HERE / "images"

# ── Carte ──────────────────────────────────────────────────────────────────────
# Coordonnées en mm, vue de dessus (côté composants), origine en bas à gauche.
# Le cuivre est sur la face dessous : le G-code est donc mis en miroir en X.
W, H = 87.0, 55.0
PITCH = 2.54
ESP_X_LEFT = 30.0
ESP_ROW_SPACING = 25.4  # entraxe des deux rangées du DevKit C V4 : à vérifier au pied à coulisse
ESP_X_RIGHT = ESP_X_LEFT + ESP_ROW_SPACING
ESP_Y_PIN1 = 52.0  # broche 1 (3V3 / GND) côté antenne, broche 19 côté USB

# Brochage DevKit C V4, antenne en haut, vue de dessus.
ESP_LEFT = ["3V3", "EN", "VP", "VN", "IO34", "IO35", "IO32", "IO33", "IO25", "IO26",
            "IO27", "IO14", "IO12", "GND", "IO13", "SD2", "SD3", "CMD", "5V"]
ESP_RIGHT = ["GND", "IO23", "IO22", "TX", "RX", "IO21", "GND", "IO19", "IO18", "IO5",
             "IO17", "IO16", "IO4", "IO0", "IO2", "IO15", "SD1", "SD0", "CLK"]
ESP_NETS = {"3V3": "3V3", "IO34": "SOL", "IO26": "POMPE", "IO27": "LUMIERE",
            "GND": "GND", "5V": "5V_ESP", "IO4": "ONEWIRE"}

TRACE_SIGNAL = 0.8
TRACE_POWER = 1.2
PAD_SMALL, DRILL_SMALL = 1.9, 1.0   # broches 2,54 mm, résistance, condensateur
PAD_SCREW, DRILL_SCREW = 2.8, 1.3   # borniers à vis 5,08 mm
MOUNT_DRILL = 3.2                   # trous de fixation M3
MOUNT_HOLES = [(5.0, 50.0), (84.0, 52.0), (7.5, 34.0), (62.0, 11.0)]
MIN_CLEARANCE = 0.4                 # écart minimal entre deux réseaux

# ── Usinage (GRBL) ─────────────────────────────────────────────────────────────
OFFSET = 5.0            # marge entre l'origine machine (coin de la plaque) et la carte
Z_SAFE = 2.0
SPINDLE = 10000
ISO_TOOL_WIDTH = 0.2    # largeur de coupe effective de la fraise en V
ISO_PASSES = 3
ISO_OVERLAP = 0.4
ISO_DEPTH = -0.1
ISO_FEED, ISO_PLUNGE = 150, 50
DRILL_DEPTH = -1.9
DRILL_FEED = 60
CUT_TOOL = 2.0          # fraise droite de découpe
CUT_DEPTH = -1.8
CUT_STEP = 0.45
CUT_FEED, CUT_PLUNGE = 150, 40
TAB_WIDTH = 3.0
TAB_Z = -1.0            # dessus des attaches : 0,6 mm de matière à casser


def esp_pin(side, i):
    """Position de la broche i (1 à 19) de la rangée gauche ou droite."""
    x = ESP_X_LEFT if side == "L" else ESP_X_RIGHT
    return (x, ESP_Y_PIN1 - (i - 1) * PITCH)


# ── Composants : (référence, broche, x, y, pastille, perçage, réseau) ─────────
pads = []
for i, name in enumerate(ESP_LEFT, 1):
    pads.append(("U1", f"G{i} {name}", *esp_pin("L", i), PAD_SMALL, DRILL_SMALL,
                 ESP_NETS.get(name, f"NC_L{i}")))
for i, name in enumerate(ESP_RIGHT, 1):
    net = ESP_NETS.get(name, f"NC_R{i}")
    if name == "GND":
        net = f"GND_ESP_R{i}"  # relié par le DevKit, pas par la carte
    pads.append(("U1", f"D{i} {name}", *esp_pin("R", i), PAD_SMALL, DRILL_SMALL, net))


def add(ref, x, ys, nets, pad, drill, names=None):
    for k, (y, net) in enumerate(zip(ys, nets)):
        pads.append((ref, names[k] if names else net, x, y, pad, drill, net))


Y = lambda i: esp_pin("L", i)[1]
# J1 capteur d'humidité (connecteur mâle 3 broches, câble Dupont)
add("J1", 12.0, [Y(5) + PITCH, Y(5), Y(5) - PITCH], ["3V3", "SOL", "GND"],
    PAD_SMALL, DRILL_SMALL, ["VCC", "AOUT", "GND"])
# J2 relais (connecteur mâle 6 broches : IN pompe, IN lumière, GND, GND, 5V, 5V)
add("J2", 12.0, [Y(10), Y(11), Y(11) - PITCH, Y(11) - 2 * PITCH, Y(11) - 3 * PITCH,
                 Y(11) - 4 * PITCH],
    ["POMPE", "LUMIERE", "GND", "GND", "5V", "5V"], PAD_SMALL, DRILL_SMALL,
    ["IN1", "IN2", "GND", "GND", "5V", "5V"])
# J3 alimentation (bornier à vis 2 points)
add("J3", 8.0, [10.5, 10.5 - 5.08], ["5V", "GND"], PAD_SCREW, DRILL_SCREW, ["+5V", "GND"])
# C1 découplage 100 µF / 10 V (radial, pas de 2,5 mm)
add("C1", 16.0, [10.5, 8.0], ["5V", "GND"], 2.0, DRILL_SMALL, ["+", "-"])
# D1 Schottky 1N5819 (DO-41, pas de 10,16 mm) : rail 5 V de la carte → broche 5V de l'ESP32.
# Avec la diode de l'USB du DevKit, l'ESP32 prend la plus haute des deux sources sans retour.
D1_X = 25.0
pads.append(("D1", "A", D1_X, Y(11) - 4 * PITCH, PAD_SCREW - 0.2, DRILL_SCREW, "5V"))
pads.append(("D1", "K", D1_X, Y(19), PAD_SCREW - 0.2, DRILL_SCREW, "5V_ESP"))
# J4, J5 sondes DS18B20 (borniers à vis 3 points)
add("J4", 77.0, [47.0, 47.0 - 5.08, 47.0 - 2 * 5.08], ["GND", "ONEWIRE", "3V3"],
    PAD_SCREW, DRILL_SCREW, ["GND", "DATA", "VCC"])
add("J5", 77.0, [29.0, 29.0 - 5.08, 29.0 - 2 * 5.08], ["3V3", "ONEWIRE", "GND"],
    PAD_SCREW, DRILL_SCREW, ["VCC", "DATA", "GND"])
# R1 4,7 kΩ de tirage du bus 1-Wire (pas de 10,16 mm)
y_ow = esp_pin("R", 13)[1]
pads.append(("R1", "1", 60.34, y_ow, 2.0, DRILL_SMALL, "ONEWIRE"))
pads.append(("R1", "2", 70.5, y_ow, 2.0, DRILL_SMALL, "3V3"))

# ── Pistes : (réseau, largeur, points) ─────────────────────────────────────────
x3v3 = 33.5          # descente du 3V3 entre les deux rangées de l'ESP32
y3v3 = 3.9           # passage du 3V3 sous la broche 19
y_gnd = 1.8          # retour de masse le long du bord bas
x_gnd_l, x_gnd_r = 3.5, 84.0
L = esp_pin
traces = [
    # 3V3 : ESP32 → humidité, puis sous l'ESP32 vers R1 et les sondes
    ("3V3", TRACE_SIGNAL, [(12, Y(4)), (20, Y(4)), (20, Y(1)), L("L", 1)]),
    ("3V3", TRACE_SIGNAL, [L("L", 1), (x3v3, Y(1)), (x3v3, y3v3), (70.5, y3v3),
                           (70.5, (36.84 + 29.0) / 2), (77, (36.84 + 29.0) / 2)]),
    ("3V3", TRACE_SIGNAL, [(77, 36.84), (77, 29.0)]),
    # Signaux
    ("SOL", TRACE_SIGNAL, [(12, Y(5)), L("L", 5)]),
    ("POMPE", TRACE_SIGNAL, [(12, Y(10)), L("L", 10)]),
    ("LUMIERE", TRACE_SIGNAL, [(12, Y(11)), L("L", 11)]),
    ("ONEWIRE", TRACE_SIGNAL, [L("R", 13), (66, y_ow), (66, 41.92), (77, 41.92)]),
    ("ONEWIRE", TRACE_SIGNAL, [(77, 41.92), (80.5, 41.92), (80.5, 23.92), (77, 23.92)]),
    # 5V
    ("5V", TRACE_POWER, [(12, Y(11) - 3 * PITCH), (12, Y(11) - 4 * PITCH)]),
    ("5V", TRACE_POWER, [(12, Y(11) - 4 * PITCH), (D1_X, Y(11) - 4 * PITCH)]),
    ("5V", TRACE_POWER, [(20, Y(11) - 4 * PITCH), (20, 10.5), (8, 10.5)]),
    ("5V_ESP", TRACE_POWER, [(D1_X, Y(19)), L("L", 19)]),
    # GND : bus à gauche, le long du bas et à droite
    ("GND", TRACE_POWER, [(12, Y(6)), (x_gnd_l, Y(6)), (x_gnd_l, y_gnd), (x_gnd_r, y_gnd),
                          (x_gnd_r, 47.0), (77, 47.0)]),
    ("GND", TRACE_POWER, [(12, Y(11) - PITCH), (x_gnd_l, Y(11) - PITCH)]),
    ("GND", TRACE_POWER, [(12, Y(11) - PITCH), (12, Y(11) - 2 * PITCH)]),
    ("GND", TRACE_POWER, [(12, Y(11) - 2 * PITCH), (22, Y(11) - 2 * PITCH), (22, Y(14)),
                          L("L", 14)]),
    ("GND", TRACE_POWER, [(8, 10.5 - 5.08), (x_gnd_l, 10.5 - 5.08)]),
    ("GND", TRACE_POWER, [(16, 8.0), (16, y_gnd)]),
    ("GND", TRACE_POWER, [(77, 18.84), (x_gnd_r, 18.84)]),
]


# ── Géométrie du cuivre et contrôles ───────────────────────────────────────────
def copper_by_net():
    shapes = {}
    for _, _, x, y, d, _, net in pads:
        shapes.setdefault(net, []).append(Point(x, y).buffer(d / 2, 32))
    for net, w, pts in traces:
        shapes.setdefault(net, []).append(LineString(pts).buffer(w / 2, 16))
    return {net: unary_union(g) for net, g in shapes.items()}


def check(copper):
    errors = []
    nets = list(copper)
    for i, a in enumerate(nets):
        if copper[a].geom_type != "Polygon":
            errors.append(f"réseau {a} non continu")
        for b in nets[i + 1:]:
            d = copper[a].distance(copper[b])
            if d < MIN_CLEARANCE:
                errors.append(f"{a} / {b} : écart {d:.2f} mm")
    board = box(0, 0, W, H)
    for net, g in copper.items():
        if not board.buffer(-0.5).contains(g):
            errors.append(f"réseau {net} trop près du bord")
    for mx, my in MOUNT_HOLES:
        hole = Point(mx, my).buffer(MOUNT_DRILL / 2 + 0.5)
        for net, g in copper.items():
            if hole.intersects(g):
                errors.append(f"trou de fixation ({mx}, {my}) touche {net}")
    for net in ("3V3", "GND", "5V", "5V_ESP", "ONEWIRE", "SOL", "POMPE", "LUMIERE"):
        pins = [f"{r}.{p}" for r, p, *_, n in pads if n == net]
        print(f"  {net:8s} {', '.join(pins)}")
    min_gap = min(copper[a].distance(copper[b])
                  for i, a in enumerate(nets) for b in nets[i + 1:])
    print(f"  écart minimal entre réseaux : {min_gap:.2f} mm")
    if errors:
        raise SystemExit("Erreurs :\n  " + "\n  ".join(errors))


# ── Gerber et Excellon ─────────────────────────────────────────────────────────
def gnum(v):
    return f"{round(v * 1e6):d}"


def write_gerber(path, function, flashes, draws):
    """flashes : [(diamètre, x, y)], draws : [(largeur, points)]"""
    apertures = {}
    for d in [f[0] for f in flashes] + [w for w, _ in draws]:
        apertures.setdefault(round(d, 3), 10 + len(apertures))
    lines = ["G04 SemiX - genere par PCB/pcb_semix.py*", f"%TF.FileFunction,{function}*%",
             "%FSLAX46Y46*%", "%MOMM*%", "%LPD*%"]
    lines += [f"%ADD{n}C,{d:.3f}*%" for d, n in apertures.items()]
    for w, pts in draws:
        lines.append(f"D{apertures[round(w, 3)]}*")
        x, y = pts[0]
        lines.append(f"X{gnum(x)}Y{gnum(y)}D02*")
        lines += [f"X{gnum(x)}Y{gnum(y)}D01*" for x, y in pts[1:]]
    for d, x, y in flashes:
        lines += [f"D{apertures[round(d, 3)]}*", f"X{gnum(x)}Y{gnum(y)}D03*"]
    lines.append("M02*")
    path.write_text("\n".join(lines) + "\n")


def write_excellon(path, holes):
    sizes = sorted({d for d, _, _ in holes})
    lines = ["M48", "; SemiX - genere par PCB/pcb_semix.py", "METRIC,TZ"]
    lines += [f"T{i}C{d:.3f}" for i, d in enumerate(sizes, 1)]
    lines += ["%", "G90", "G05"]
    for i, d in enumerate(sizes, 1):
        lines.append(f"T{i}")
        lines += [f"X{x:.3f}Y{y:.3f}" for dd, x, y in holes if dd == d]
    lines.append("M30")
    path.write_text("\n".join(lines) + "\n")


# ── G-code ─────────────────────────────────────────────────────────────────────
def mx(x, y):
    """Vue de dessus → repère machine, carte retournée cuivre vers le haut."""
    return OFFSET + (W - x), OFFSET + y


def header(title, tool):
    return [f"( SemiX - {title} )", f"( Outil : {tool} )",
            "( Z0 = surface du cuivre, X0 Y0 = coin avant gauche de la plaque )",
            f"( Carte {W:.0f} x {H:.0f} mm placee a {OFFSET:.0f} mm de l'origine, vue cote cuivre )",
            "G21 G90 G94", "G17", f"G0 Z{Z_SAFE:.3f}", f"M3 S{SPINDLE}", "G4 P3"]


FOOTER = [f"G0 Z{Z_SAFE + 8:.3f}", "M5", "G0 X0 Y0", "M30"]


def order_paths(paths, start=(0.0, 0.0)):
    """Plus proche voisin pour réduire les déplacements à vide."""
    remaining, ordered, pos = list(paths), [], start
    while remaining:
        k = min(range(len(remaining)),
                key=lambda i: (remaining[i][0][0] - pos[0]) ** 2 + (remaining[i][0][1] - pos[1]) ** 2)
        p = remaining.pop(k)
        ordered.append(p)
        pos = p[-1]
    return ordered


def rings(geom):
    polys = getattr(geom, "geoms", [geom])
    out = []
    for p in polys:
        out.append(list(p.exterior.coords))
        out += [list(r.coords) for r in p.interiors]
    return out


def isolation_paths(copper):
    all_cu = list(copper.values())
    paths = []
    for k in range(ISO_PASSES):
        r = ISO_TOOL_WIDTH / 2 + k * ISO_TOOL_WIDTH * (1 - ISO_OVERLAP)
        g = unary_union([c.buffer(r, 16) for c in all_cu]).simplify(0.01)
        paths += rings(g)
    return paths


def gcode_isolation(paths):
    g = header("isolation des pistes", f"fraise V, coupe {ISO_TOOL_WIDTH} mm, "
               f"profondeur {-ISO_DEPTH} mm, {ISO_PASSES} passes")
    mpaths = order_paths([[mx(x, y) for x, y in p] for p in paths])
    for p in mpaths:
        g.append(f"G0 X{p[0][0]:.3f} Y{p[0][1]:.3f}")
        g.append(f"G1 Z{ISO_DEPTH:.3f} F{ISO_PLUNGE}")
        g += [f"G1 X{x:.3f} Y{y:.3f} F{ISO_FEED}" for x, y in p[1:]]
        g.append(f"G0 Z{Z_SAFE:.3f}")
    return g + FOOTER, mpaths


def gcode_drill(holes, d):
    g = header(f"percage {d} mm", f"foret {d} mm")
    pts = order_paths([[mx(x, y)] for dd, x, y in holes if dd == d])
    for (p,) in pts:
        g += [f"G0 X{p[0]:.3f} Y{p[1]:.3f}", f"G1 Z{DRILL_DEPTH:.3f} F{DRILL_FEED}",
              f"G0 Z{Z_SAFE:.3f}"]
    return g + FOOTER


def depths():
    z, out = 0.0, []
    while z > CUT_DEPTH + 1e-9:
        z = max(z - CUT_STEP, CUT_DEPTH)
        out.append(round(z, 3))
    return out


def gcode_cutout():
    r = CUT_TOOL / 2
    g = header("trous de fixation et detourage", f"fraise droite {CUT_TOOL} mm")
    previews = []
    # Trous de fixation : cercle intérieur, passes successives
    for hx, hy in MOUNT_HOLES:
        cx, cy = mx(hx, hy)
        rr = MOUNT_DRILL / 2 - r
        g += [f"G0 X{cx + rr:.3f} Y{cy:.3f}"]
        for z in depths():
            g += [f"G1 Z{z:.3f} F{CUT_PLUNGE}", f"G2 X{cx + rr:.3f} Y{cy:.3f} I{-rr:.3f} J0 F{CUT_FEED}"]
        g.append(f"G0 Z{Z_SAFE:.3f}")
        previews.append(Point(cx, cy).buffer(rr, 32).exterior.coords)
    # Contour extérieur, sens horaire (fraisage en avalant sur l'extérieur), avec 4 attaches
    outline = box(OFFSET, OFFSET, OFFSET + W, OFFSET + H).buffer(r, 8).exterior
    ring = LineString(list(outline.coords)[::-1] if outline.is_ccw else outline.coords)
    tabs = []
    for tx, ty in [(OFFSET + W / 2, OFFSET), (OFFSET + W / 2, OFFSET + H),
                   (OFFSET, OFFSET + H / 2), (OFFSET + W, OFFSET + H / 2)]:
        s = ring.project(Point(tx, ty))
        half = (TAB_WIDTH + CUT_TOOL) / 2
        tabs.append((s - half, s + half))
    tabs.sort()
    cuts, s0 = [], 0.0
    for a, b in tabs:
        cuts.append((s0, a, False))
        cuts.append((a, b, True))
        s0 = b
    cuts.append((s0, ring.length, False))
    x0, y0 = ring.coords[0]
    g.append(f"G0 X{x0:.3f} Y{y0:.3f}")
    for z in depths():
        g.append(f"G1 Z{min(z, 0):.3f} F{CUT_PLUNGE}")
        for a, b, is_tab in cuts:
            seg = list(substring(ring, a, b).coords)
            zz = max(z, TAB_Z) if is_tab else z
            g.append(f"G1 Z{zz:.3f} F{CUT_PLUNGE}")
            g += [f"G1 X{x:.3f} Y{y:.3f} F{CUT_FEED}" for x, y in seg[1:]]
    g.append(f"G0 Z{Z_SAFE:.3f}")
    previews.append(ring.coords)
    return g + FOOTER, previews


# ── Images ─────────────────────────────────────────────────────────────────────
NET_COLORS = {"GND": "#3a3a3a", "5V": "#c0392b", "5V_ESP": "#e74c3c", "3V3": "#e67e22", "ONEWIRE": "#2e86c1",
              "SOL": "#27ae60", "POMPE": "#8e44ad", "LUMIERE": "#b7950b"}

LABELS = [  # (x, y, texte, alignement)
    (2.0, Y(5), "J1 humidité\nVCC\nAOUT\nGND", "left"),
    (2.0, Y(12), "J2 relais\nIN1 pompe\nIN2 lumière\nGND GND\n5V 5V", "left"),
    (2.0, 7.9, "J3 alim. 5 V\n+5V\nGND", "left"),
    (85.0, 41.9, "J4 DS18B20\nréservoir\nGND\nDATA\nVCC", "right"),
    (85.0, 23.9, "J5 DS18B20\nsemis\nVCC\nDATA\nGND", "right"),
]


def draw_layout(copper, path):
    fig, ax = plt.subplots(figsize=(11, 7.6), dpi=150)
    ax.add_patch(Rectangle((0, 0), W, H, fc="#e9dfc6", ec="#6b5b3e", lw=1.5))
    for net, g in copper.items():
        color = NET_COLORS.get(net, "#b08d57")
        for p in getattr(g, "geoms", [g]):
            ax.fill(*p.exterior.xy, color=color, alpha=0.35 if net in NET_COLORS else 0.25, lw=0)
    # Contours des composants (vue de dessus)
    ax.add_patch(FancyBboxPatch((ESP_X_LEFT - 1.3, Y(19) - 2.5), ESP_ROW_SPACING + 2.6,
                                54.4, boxstyle="round,pad=0,rounding_size=1", fc="none",
                                ec="#1b4f72", lw=1.4, ls="--"))
    ax.text(ESP_X_LEFT + ESP_ROW_SPACING / 2, 30, "U1\nESP32\nDevKit C V4\n\nantenne ↑\nUSB ↓",
            ha="center", va="center", fontsize=9, color="#1b4f72")
    for x, y0, y1 in [(12, Y(4) + 1.27, Y(6) - 1.27), (12, Y(10) + 1.27, Y(11) - 4 * PITCH - 1.27)]:
        ax.add_patch(Rectangle((x - 1.27, y1), 2.54, y0 - y1, fc="none", ec="k", lw=1))
    for x, yc, n, front in [(8, 7.96, 2, -1), (77, 41.92, 3, 1), (77, 23.92, 3, 1)]:
        h = n * 5.08
        back = x - 3.3 * front
        ax.add_patch(Rectangle((min(back, x + 4.3 * front), yc - h / 2), 7.6, h,
                               fc="#2ecc71", alpha=0.25, ec="#1e8449", lw=1))
    ax.add_patch(Circle((16, 9.25), 3.15, fc="none", ec="k", lw=1))
    ax.text(16, 13.2, "C1 100µF", ha="center", fontsize=7)
    ax.text(16, 9.25, "+\n\n−", ha="left", va="center", fontsize=7)
    yd = (Y(11) - 4 * PITCH + Y(19)) / 2
    ax.add_patch(Rectangle((D1_X - 1.35, yd - 2.6), 2.7, 5.2, fc="#555", ec="k", lw=1))
    ax.add_patch(Rectangle((D1_X - 1.35, yd - 2.6), 2.7, 0.9, fc="#ddd", ec="none"))
    ax.text(D1_X + 1.8, yd, "D1\n1N5819", ha="left", va="center", fontsize=7)
    ax.add_patch(Rectangle((62.4, y_ow - 1.2), 6.0, 2.4, fc="#f5cba7", ec="k", lw=1))
    ax.text(65.4, y_ow - 3.2, "R1 4,7 kΩ", ha="center", fontsize=7)
    for _, _, x, y, d, drill, net in pads:
        ax.add_patch(Circle((x, y), d / 2, fc="#c9a227", ec="#7d6608", lw=0.6))
        ax.add_patch(Circle((x, y), drill / 2, fc="white", ec="none"))
    for x, y in MOUNT_HOLES:
        ax.add_patch(Circle((x, y), MOUNT_DRILL / 2, fc="white", ec="k", lw=1))
    for x, y, t, ha in LABELS:
        ax.text(x, y, t, ha=ha, va="center", fontsize=7.5, linespacing=1.15,
                bbox=dict(fc="white", ec="none", alpha=0.7, pad=1))
    for side, names in (("L", ESP_LEFT), ("R", ESP_RIGHT)):
        for i, name in enumerate(names, 1):
            x, y = esp_pin(side, i)
            ax.text(x + (1.6 if side == "L" else -1.6), y, name, fontsize=4.5,
                    ha="left" if side == "L" else "right", va="center", color="#1b4f72")
    handles = [Rectangle((0, 0), 1, 1, fc=c, alpha=0.6) for c in NET_COLORS.values()]
    ax.legend(handles, ["GND", "5 V", "5 V ESP32", "3,3 V", "1-Wire (GPIO4)", "Humidité (GPIO34)",
                        "Pompe (GPIO26)", "Lumière (GPIO27)"],
              loc="upper center", bbox_to_anchor=(0.5, -0.03), ncol=8, fontsize=7, frameon=False)
    ax.set_title("Implantation, vue côté composants (pistes vues par transparence)", fontsize=11)
    ax.set_xlim(-1, W + 1)
    ax.set_ylim(-1, H + 1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def draw_toolpaths(copper, iso, cut, holes, path):
    fig, ax = plt.subplots(figsize=(11, 7.6), dpi=150)
    ax.add_patch(Rectangle((0, 0), W + 2 * OFFSET, H + 2 * OFFSET, fc="#d9d9d9", ec="#999"))
    ax.add_patch(Rectangle((OFFSET, OFFSET), W, H, fc="#d4a35a", ec="none"))
    for g in copper.values():
        for p in getattr(g, "geoms", [g]):
            xs, ys = zip(*[mx(x, y) for x, y in p.exterior.coords])
            ax.fill(xs, ys, color="#b5651d", lw=0)
    for p in iso:
        xs, ys = zip(*p)
        ax.plot(xs, ys, color="#1f3a93", lw=0.45)
    for p in cut:
        xs, ys = zip(*p)
        ax.plot(xs, ys, color="#c0392b", lw=1.0)
    for d, x, y in holes:
        if d != MOUNT_DRILL:
            ax.add_patch(Circle(mx(x, y), d / 2, fc="white", ec="k", lw=0.4))
    ax.annotate("X0 Y0", (0, 0), (3, -5), textcoords="offset points", fontsize=8)
    ax.set_title("Usinage, vue côté cuivre (miroir) : isolation en bleu, découpe en rouge",
                 fontsize=11)
    ax.set_xlim(-2, W + 2 * OFFSET + 2)
    ax.set_ylim(-3, H + 2 * OFFSET + 2)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# ── Programme principal ────────────────────────────────────────────────────────
def main():
    copper = copper_by_net()
    print("Contrôle des réseaux :")
    check(copper)

    gerber, gcode = OUT / "gerber", OUT / "gcode"
    for d in (gerber, gcode, IMG):
        d.mkdir(parents=True, exist_ok=True)

    write_gerber(gerber / "SemiX-B_Cu.gbl", "Copper,L2,Bot",
                 [(d, x, y) for _, _, x, y, d, _, _ in pads],
                 [(w, pts) for _, w, pts in traces])
    write_gerber(gerber / "SemiX-Edge_Cuts.gm1", "Profile,NP",
                 [], [(0.1, [(0, 0), (W, 0), (W, H), (0, H), (0, 0)])])
    holes = [(drill, x, y) for _, _, x, y, _, drill, _ in pads]
    holes += [(MOUNT_DRILL, x, y) for x, y in MOUNT_HOLES]
    write_excellon(gerber / "SemiX.drl", holes)

    iso_g, iso_paths = gcode_isolation(isolation_paths(copper))
    (gcode / "1_isolation_fraiseV.nc").write_text("\n".join(iso_g) + "\n")
    drills = sorted({d for d, _, _ in holes if d != MOUNT_DRILL})
    for k, d in enumerate(drills, 2):
        (gcode / f"{k}_percage_{d:.1f}mm.nc").write_text("\n".join(gcode_drill(holes, d)) + "\n")
    cut_g, cut_paths = gcode_cutout()
    (gcode / f"{len(drills) + 2}_detourage_fraise{CUT_TOOL:.0f}mm.nc").write_text("\n".join(cut_g) + "\n")

    draw_layout(copper, IMG / "pcb_implantation.png")
    draw_toolpaths(copper, iso_paths, cut_paths, holes, IMG / "pcb_usinage.png")
    for d in drills:
        print(f"  perçage {d} mm : {sum(1 for dd, *_ in holes if dd == d)} trous")
    print(f"Fichiers écrits dans {OUT} et {IMG}")


if __name__ == "__main__":
    main()
