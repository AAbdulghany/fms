"""Refine Orbit concepts A and B: rounded terminals + stacked Orbit lockup."""
import json
import math
import re
from pathlib import Path

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

out = Path(__file__).resolve().parent
font = TTFont(Path(__file__).resolve().parents[3] / ".venv/Lib/site-packages/reportlab/fonts/Vera.ttf")
glyphset = font.getGlyphSet()


class CmdPen(BasePen):
    def __init__(self, gs):
        super().__init__(gs)
        self.cmds = []

    def _moveTo(self, p):
        self.cmds.append(("M", p))

    def _lineTo(self, p):
        self.cmds.append(("L", p))

    def _curveToOne(self, p1, p2, p3):
        self.cmds.append(("C", p1, p2, p3))

    def _qCurveToOne(self, p1, p2):
        self.cmds.append(("Q", p1, p2))

    def _closePath(self):
        self.cmds.append(("Z",))


def glyph_cmds(name):
    pen = CmdPen(glyphset)
    glyphset[name].draw(pen)
    return pen.cmds, glyphset[name].width


def fnum(n):
    return f"{n:.2f}".rstrip("0").rstrip(".")


def pt(cx, cy, r, deg):
    a = math.radians(deg)
    return cx + r * math.cos(a), cy - r * math.sin(a)


def ring(cx, cy, R, r, a0, a1):
    span = (a1 - a0) % 360 or 360
    large = 1 if span > 180 else 0
    ox0, oy0 = pt(cx, cy, R, a0)
    ox1, oy1 = pt(cx, cy, R, a1)
    ix0, iy0 = pt(cx, cy, r, a0)
    ix1, iy1 = pt(cx, cy, r, a1)
    return (
        f"M {fnum(ox0)} {fnum(oy0)} A {fnum(R)} {fnum(R)} 0 {large} 0 {fnum(ox1)} {fnum(oy1)} "
        f"L {fnum(ix1)} {fnum(iy1)} A {fnum(r)} {fnum(r)} 0 {large} 1 {fnum(ix0)} {fnum(iy0)} Z"
    )


def circle(cx, cy, r):
    return (
        f"M {fnum(cx - r)} {fnum(cy)} A {fnum(r)} {fnum(r)} 0 1 0 {fnum(cx + r)} {fnum(cy)} "
        f"A {fnum(r)} {fnum(r)} 0 1 0 {fnum(cx - r)} {fnum(cy)} Z"
    )


def round_rect(x, y, w, h, rx):
    return (
        f"M {fnum(x + rx)} {fnum(y)} H {fnum(x + w - rx)} A {rx} {rx} 0 0 1 {fnum(x + w)} {fnum(y + rx)} "
        f"V {fnum(y + h - rx)} A {rx} {rx} 0 0 1 {fnum(x + w - rx)} {fnum(y + h)} H {fnum(x + rx)} "
        f"A {rx} {rx} 0 0 1 {fnum(x)} {fnum(y + h - rx)} V {fnum(y + rx)} "
        f"A {rx} {rx} 0 0 1 {fnum(x + rx)} {fnum(y)} Z"
    )


def stroked(cx, cy, mid, thick, a0, a1):
    cap = thick / 2
    c0 = pt(cx, cy, mid, a0)
    c1 = pt(cx, cy, mid, a1)
    return [
        ring(cx, cy, mid + cap, mid - cap, a0, a1),
        circle(*c0, cap),
        circle(*c1, cap),
    ]


def contours_of(cmds, x, scale, baseline):
    contours = []
    cur = []
    pts_all = []
    for cmd in cmds:
        if cmd[0] == "Z":
            cur.append("Z")
            contours.append((" ".join(cur), pts_all))
            cur, pts_all = [], []
            continue
        mapped = []
        for px, py in cmd[1:]:
            X, Y = x + px * scale, baseline - py * scale
            mapped.append(f"{fnum(X)} {fnum(Y)}")
            pts_all.append((X, Y))
        if cmd[0] == "M":
            cur.append("M " + mapped[0])
        elif cmd[0] == "L":
            cur.append("L " + mapped[0])
        elif cmd[0] == "Q":
            cur.append("Q " + " ".join(mapped))
        elif cmd[0] == "C":
            cur.append("C " + " ".join(mapped))
    return contours


# Pulls (font units) after O, r, b, i, t — tighter round-to-straight pairs.
KERN = [260, 20, 150, 10, 0]


def layout_letters(scale, origin_x, baseline, dot_fill):
    paths = []
    x = origin_x
    for i, name in enumerate(["O", "r", "b", "i", "t"]):
        cmds, width = glyph_cmds(name)
        contours = contours_of(cmds, x, scale, baseline)
        if name == "i" and len(contours) >= 2:
            def area(c):
                xs = [p[0] for p in c[1]]
                ys = [p[1] for p in c[1]]
                return (max(xs) - min(xs)) * (max(ys) - min(ys))

            contours = sorted(contours, key=area, reverse=True)
            paths.append((contours[0][0], None))
            sxs = [p[0] for p in contours[0][1]]
            xs = [p[0] for p in contours[1][1]]
            ys = [p[1] for p in contours[1][1]]
            cx = (min(sxs) + max(sxs)) / 2
            cy = (min(ys) + max(ys)) / 2
            side = max(max(xs) - min(xs), max(ys) - min(ys)) * 1.05
            paths.append((round_rect(cx - side / 2, cy - side / 2, side, side, side * 0.28), dot_fill))
        else:
            paths.append((" ".join(c[0] for c in contours), None))
        paths_width_pull = KERN[i] if i < len(KERN) else 0
        x += (width - paths_width_pull) * scale
    return paths, x - origin_x


def measure(scale):
    _, w = layout_letters(scale, 0, 0, "#000")
    return w


SCALE = 262 / measure(1)

A_MID, A_THICK, A_ANG, A_GAP = 86, 34, 56, 64
a_ring = stroked(128, 128, A_MID, A_THICK, A_ANG + A_GAP / 2, A_ANG - A_GAP / 2 + 360)
ax, ay = pt(128, 128, A_MID, A_ANG)
ay -= 2
TILE = 46
a_tile = round_rect(ax - TILE / 2, ay - TILE / 2, TILE, TILE, 14)

B_MID, B_THICK = 88, 30
b_arcs = [stroked(128, 128, B_MID, B_THICK, s, s + span) for s, span in ((39, 102), (171, 84), (285, 84))]


def bake(d, sx, sy, sc):
    tokens = re.findall(r"[A-Za-z]|-?\d*\.?\d+(?:e[-+]?\d+)?", d)
    out_cmds = []
    i = 0
    cx = cy = 0

    def num():
        nonlocal i
        v = float(tokens[i])
        i += 1
        return v

    while i < len(tokens):
        t = tokens[i]
        i += 1
        if t == "Z":
            out_cmds.append("Z")
            continue
        if t == "M":
            x, y = num(), num()
            cx, cy = sx + x * sc, sy + y * sc
            out_cmds.append(f"M {fnum(cx)} {fnum(cy)}")
        elif t == "L":
            x, y = num(), num()
            cx, cy = sx + x * sc, sy + y * sc
            out_cmds.append(f"L {fnum(cx)} {fnum(cy)}")
        elif t == "H":
            x = num()
            cx = sx + x * sc
            out_cmds.append(f"L {fnum(cx)} {fnum(cy)}")
        elif t == "V":
            y = num()
            cy = sy + y * sc
            out_cmds.append(f"L {fnum(cx)} {fnum(cy)}")
        elif t == "A":
            rx, ry, ang, large, sweep, x, y = (num() for _ in range(7))
            cx, cy = sx + x * sc, sy + y * sc
            out_cmds.append(
                f"A {fnum(rx * sc)} {fnum(ry * sc)} {fnum(ang)} {int(large)} {int(sweep)} {fnum(cx)} {fnum(cy)}"
            )
        elif t == "Q":
            x1, y1, x, y = num(), num(), num(), num()
            cx, cy = sx + x * sc, sy + y * sc
            out_cmds.append(f"Q {fnum(sx + x1 * sc)} {fnum(sy + y1 * sc)} {fnum(cx)} {fnum(cy)}")
        elif t == "C":
            vals = [num() for _ in range(6)]
            mapped = []
            for k in range(0, 6, 2):
                mapped += [fnum(sx + vals[k] * sc), fnum(sy + vals[k + 1] * sc)]
            cx, cy = sx + vals[4] * sc, sy + vals[5] * sc
            out_cmds.append("C " + " ".join(mapped))
        else:
            raise SystemExit(f"bad token {t}")
    return " ".join(out_cmds)


def lockup(colored, word_fill, dot_fill, title):
    pad = 24
    gap = 22
    ww = measure(SCALE)
    canvas_w = max(256, ww) + pad * 2
    sym_x = (canvas_w - 256) / 2
    sym_y = 8
    word_x = (canvas_w - ww) / 2
    baseline = sym_y + 256 + gap + 70
    canvas_h = baseline + 36 * SCALE + 10
    letters, _ = layout_letters(SCALE, word_x, baseline, dot_fill)
    baked = [{"d": bake(d, sym_x, sym_y, 1), "fill": fill} for d, fill in colored]
    baked += [{"d": d, "fill": fill or word_fill} for d, fill in letters]
    elems = "\n  ".join(f'<path fill="{p["fill"]}" d="{p["d"]}"/>' for p in baked)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fnum(canvas_w)} {fnum(canvas_h)}" role="img">\n'
        f"  <title>{title}</title>\n  {elems}\n</svg>\n"
    )
    return svg, baked, canvas_w, canvas_h


def symbol_svg(colored, title):
    body = "\n  ".join(f'<path fill="{fill}" d="{d}"/>' for d, fill in colored)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img">\n'
        f"  <title>{title}</title>\n  {body}\n</svg>\n"
    )


def main():
    a_colored = [(d, "#1B3A4B") for d in a_ring] + [(a_tile, "#E07A3D")]
    b_colored = []
    for arcs, col in zip(b_arcs, ("#D97706", "#0F4C4A", "#0F4C4A")):
        for d in arcs:
            b_colored.append((d, col))
    (out / "a-periapsis-v2.svg").write_text(symbol_svg(a_colored, "Orbit Periapsis"), encoding="utf-8")
    (out / "b-shift-v2.svg").write_text(symbol_svg(b_colored, "Orbit Shift"), encoding="utf-8")
    for name, colored, ink, dot in (
        ("a", a_colored, "#1B3A4B", "#E07A3D"),
        ("b", b_colored, "#0F4C4A", "#D97706"),
    ):
        svg, baked, w, h = lockup(colored, ink, dot, f"Orbit {name} lockup")
        (out / f"{name}-lockup-v2.svg").write_text(svg, encoding="utf-8")
        (out / f"{name}-lockup-v2.json").write_text(json.dumps({"w": w, "h": h, "paths": baked}), encoding="utf-8")
        print(name, round(w, 1), round(h, 1), len(baked))


if __name__ == "__main__":
    main()
