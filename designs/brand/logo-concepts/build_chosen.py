"""Chosen Periapsis lockup: Syne Bold, all caps, Signal Night palette."""
import json
import math
import re
from pathlib import Path

from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent
INK = "#1E2A4A"
SIGNAL = "#F5A524"
font = TTFont(ROOT / "fonts" / "Syne-Bold.ttf")
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


def fnum(n):
    s = f"{n:.2f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def glyph_cmds(name):
    pen = CmdPen(glyphset)
    glyphset[name].draw(pen)
    return pen.cmds, glyphset[name].width


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
        f"M {fnum(x + rx)} {fnum(y)} L {fnum(x + w - rx)} {fnum(y)} "
        f"A {fnum(rx)} {fnum(rx)} 0 0 1 {fnum(x + w)} {fnum(y + rx)} "
        f"L {fnum(x + w)} {fnum(y + h - rx)} A {fnum(rx)} {fnum(rx)} 0 0 1 {fnum(x + w - rx)} {fnum(y + h)} "
        f"L {fnum(x + rx)} {fnum(y + h)} A {fnum(rx)} {fnum(rx)} 0 0 1 {fnum(x)} {fnum(y + h - rx)} "
        f"L {fnum(x)} {fnum(y + rx)} A {fnum(rx)} {fnum(rx)} 0 0 1 {fnum(x + rx)} {fnum(y)} Z"
    )


def stroked(cx, cy, mid, thick, a0, a1):
    cap = thick / 2
    return [
        ring(cx, cy, mid + cap, mid - cap, a0, a1),
        circle(*pt(cx, cy, mid, a0), cap),
        circle(*pt(cx, cy, mid, a1), cap),
    ]


def emit(cmds, x, scale, baseline):
    parts = []
    for cmd in cmds:
        if cmd[0] == "Z":
            parts.append("Z")
            continue
        mapped = [f"{fnum(x + px * scale)} {fnum(baseline - py * scale)}" for px, py in cmd[1:]]
        parts.append(cmd[0] + " " + " ".join(mapped))
    return " ".join(parts)


# Pulls after O, R, B, I, T in font units.
KERN = [90, 40, 70, -10, 0]


def layout(scale, origin_x, baseline):
    paths = []
    x = origin_x
    for i, name in enumerate("ORBIT"):
        cmds, width = glyph_cmds(name)
        paths.append(emit(cmds, x, scale, baseline))
        x += (width - KERN[i]) * scale
    return paths, x - origin_x


def measure(scale):
    _, w = layout(scale, 0, 0)
    return w


SCALE = 268 / measure(1)
A_MID, A_THICK, A_ANG, A_GAP = 86, 34, 56, 64
a_ring = stroked(128, 128, A_MID, A_THICK, A_ANG + A_GAP / 2, A_ANG - A_GAP / 2 + 360)
ax, ay = pt(128, 128, A_MID, A_ANG)
ay -= 2
TILE = 46
a_tile = round_rect(ax - TILE / 2, ay - TILE / 2, TILE, TILE, 14)


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
        if t in ("M", "L"):
            x, y = num(), num()
            cx, cy = sx + x * sc, sy + y * sc
            out_cmds.append(f"{t} {fnum(cx)} {fnum(cy)}")
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


def main():
    colored = [(d, INK) for d in a_ring] + [(a_tile, SIGNAL)]
    pad, gap = 28, 26
    ww = measure(SCALE)
    canvas_w = max(256, ww) + pad * 2
    sym_x = (canvas_w - 256) / 2
    sym_y = 8
    word_x = (canvas_w - ww) / 2
    baseline = sym_y + 256 + gap + 64
    canvas_h = baseline + 18
    letters = layout(SCALE, word_x, baseline)[0]
    baked = [{"d": bake(d, sym_x, sym_y, 1), "fill": fill} for d, fill in colored]
    baked += [{"d": d, "fill": INK} for d in letters]
    elems = "\n  ".join(f'<path fill="{p["fill"]}" d="{p["d"]}"/>' for p in baked)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fnum(canvas_w)} {fnum(canvas_h)}" role="img">\n'
        f"  <title>Orbit Periapsis lockup</title>\n  {elems}\n</svg>\n"
    )
    (ROOT / "orbit-lockup.svg").write_text(svg, encoding="utf-8")
    (ROOT / "orbit-lockup.json").write_text(
        json.dumps({"w": round(canvas_w), "h": round(canvas_h), "ink": INK, "signal": SIGNAL, "paths": baked}),
        encoding="utf-8",
    )
    sym = "\n  ".join(f'<path fill="{fill}" d="{d}"/>' for d, fill in colored)
    (ROOT / "orbit-symbol.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256" role="img">\n'
        f"  <title>Orbit symbol</title>\n  {sym}\n</svg>\n",
        encoding="utf-8",
    )
    print("canvas", round(canvas_w), round(canvas_h), "paths", len(baked), "word", round(ww, 1))


if __name__ == "__main__":
    main()
