"""Make the menu graphics Blasphemer left as placeholders.

usage: python3 make_menu.py <blasphem.wad> <graphics dir>

From the WAD's own art, in its palette, writes for wadinfo.txt and BlasphDM.txt:
  m_skl00.png ... m_skl17.png  M_SKL00-17  the medallion spinning beside
                                            the main menu's title (PSKULL)
  m_fslot.png                  M_FSLOT     a save slot, cut into the status
                                            bar's stone (BARBACK)
  m_sldlt.png, m_sldmd1.png,   M_SLDLT ... the slider's ends and groove, in
  m_sldmd2.png, m_sldrt.png    M_SLDRT     the same stone
Offsets go in wadinfo.txt; the comments below say what they are.
"""
import math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wad import Wad
from PIL import Image

wad = Wad(sys.argv[1]); out = sys.argv[2]
pal = wad.palette()
cm = wad.lump("COLORMAP")
colormap = [cm[i * 256:(i + 1) * 256] for i in range(32)]
TRANSPARENT = (0, 47, 47)  # deutex's default


def save(rows, name):
    """rows: lists of palette indices, None where transparent."""
    h, w = len(rows), len(rows[0])
    im = Image.new("RGB", (w, h))
    im.putdata([TRANSPARENT if c is None else pal[c] for r in rows for c in r])
    im.save(os.path.join(out, name))


def shade(c, level):
    """Darken (level > 0) through COLORMAP, or brighten (level < 0) by
    finding the colormap entry that darkens to c; keeps the hue."""
    if level >= 0:
        return colormap[min(31, level)][c]
    best = c
    for k in range(1, -level + 1):
        ups = [i for i in range(256) if colormap[k][i] == c and i != c]
        if ups:
            best = min(ups, key=lambda i: -sum(pal[i]))
    return best


# ---- M_SKL00-17: PSKULL spinning about its upright axis.  The main menu
# draws frame f on the right and 17 - f on the left, three tics apiece, so
# the two turn opposite ways.  The front is PSKULL3, whose eyes burn and stay
# lit; the back is PSKULL1 with dark eyes, mirrored as seen from behind.  The
# medallion is a slab, drawn as slices from back to front.
CANVAS = 44   # wadinfo offsets -2 6: centres it in the 48 pixels beside M_HTIC
DEPTH = 4
fw, fh, _, _, front = wad.patch("PSKULL3")
_, _, _, _, plain = wad.patch("PSKULL1")
back = [list(reversed(r)) for r in plain]
burning = {c for r in front for c in r if c is not None and (136 <= c <= 144 or 240 <= c <= 247)}
cx = (fw - 1) / 2
for f in range(18):
    th = 2 * math.pi * f / 18
    c, s = math.cos(th), math.sin(th)
    rows = [[None] * CANVAS for _ in range(fh)]
    depth = [[-1e9] * CANVAS for _ in range(fh)]
    lit = lambda nx, nz: max(0.0, 0.9 * nz - 0.45 * nx)  # light from the front left
    steps = DEPTH * 4
    for k in range(steps + 1):
        z = -DEPTH / 2 + DEPTH * k / steps
        for y in range(fh):
            for x in range(fw):
                p = front[y][x]
                if p is None:
                    continue
                if k == steps and c > 0:
                    col = p if p in burning else colormap[round((1 - lit(s, c)) * 22)][p]
                elif k == 0 and c < 0:
                    q = back[y][x] if back[y][x] is not None else p
                    col = colormap[min(31, round((1 - 0.7 * lit(-s, -c)) * 22))][q]
                else:   # the edge
                    col = colormap[round((0.75 - 0.35 * abs(s)) * 22)][p]
                u0 = (x - 0.5 - cx) * c + z * s
                u1 = (x + 0.5 - cx) * c + z * s
                u0, u1 = min(u0, u1), max(u0, u1)
                d = -(x - cx) * s + z * c
                a = math.floor(u0 + CANVAS / 2 + 0.5)
                b = max(a, math.floor(u1 + CANVAS / 2 + 0.5) - 1)
                for u in range(a, b + 1):
                    if 0 <= u < CANVAS and d >= depth[y][u]:
                        depth[y][u] = d
                        rows[y][u] = col
    save(rows, f"m_skl{f:02d}.png")


# ---- the status bar's plain stone, to cut the slot and the slider from
_, _, _, _, bar = wad.patch("BARBACK")
stone_tiles = [[r[x0:x0 + 48] for r in bar[4:40]] for x0 in (100, 170)]
rng = random.Random(7)


def stone(w, h, tile=0):
    """w x h of the stone, tiled (mirrored on alternate tiles) from BARBACK."""
    t = stone_tiles[tile]
    th, tw = len(t), len(t[0])
    ox, oy = rng.randrange(tw), rng.randrange(th)
    rows = []
    for y in range(h):
        yy = (y + oy) % (2 * th); yy = yy if yy < th else 2 * th - 1 - yy
        row = []
        for x in range(w):
            xx = (x + ox) % (2 * tw); xx = xx if xx < tw else 2 * tw - 1 - xx
            row.append(t[yy][xx])
        rows.append(row)
    return rows


# the menu font's colours: silver greys outlined in dark brown
OUTLINE = 68
LIT, LIT2, MID, DARK2, DARK = 27, 22, 19, 16, 13


def frame(rows, x0, y0, x1, y1):
    """A silver frame, lit from the top left, outlined inside and out."""
    for i, (lit, dark) in enumerate([(OUTLINE, OUTLINE), (LIT, DARK), (LIT2, DARK2),
                                     (OUTLINE, OUTLINE)]):
        a0, b0, a1, b1 = x0 + i, y0 + i, x1 - 1 - i, y1 - 1 - i
        for x in range(a0, a1 + 1):
            rows[b0][x] = lit
            rows[b1][x] = dark
        for y in range(b0, b1 + 1):
            rows[y][a0] = lit if y < b1 else dark
            rows[y][a1] = dark if y > b0 else lit


def darken(rows, x0, y0, x1, y1, level):
    for y in range(y0, y1):
        for x in range(x0, x1):
            rows[y][x] = colormap[level][rows[y][x]]


# ---- M_FSLOT: 180 x 18, centred under the save menu's x of 70.  Names are
# written in FONTA at (5, 5), inside the frame, on the stone.
slot = stone(180, 18)
darken(slot, 0, 0, 180, 18, 2)
frame(slot, 0, 0, 180, 18)
save(slot, "m_fslot.png")


# ---- the slider: DrawSlider puts M_SLDLT at x - 32, then M_SLDMD1 and 2 in
# turn, 8 apiece, from x, and M_SLDRT after them; the knob (M_SLDKB, offsets
# 4 4) at x + 4 + 8 * value, y + 7, so the groove's middle is row 8.  The ends
# are 12 wide: M_SLDLT's offsets -20 0 put it against the rail.
H = 16


def rail(tile, tick):
    """8 pixels of a silver rail with the stone showing in its groove; every
    other piece has a tick below it."""
    rows = [[None] * 8 for _ in range(H)]
    st = stone(8, H, tile)
    colours = {3: OUTLINE, 4: LIT, 5: MID, 6: OUTLINE, 11: DARK2, 12: DARK, 13: OUTLINE}
    for y in range(3, 14):
        for x in range(8):
            rows[y][x] = colours.get(y, colormap[3][st[y][x]])
    if tick:
        rows[14][0] = rows[15][0] = MID
    return rows


def end(right):
    """A silver block with a blood-red jewel set in it."""
    w = 12
    rows = [[None] * w for _ in range(H)]
    for y in range(1, 15):
        for x in range(w):
            rows[y][x] = MID
    frame(rows, 0, 1, w, 15)
    for y in range(4, 12):
        for x in range(4, w - 4):
            rows[y][x] = DARK2
    for dx, dy, c in [(0, -1, 157), (-1, 0, 154), (0, 0, 160), (1, 0, 151), (0, 1, 149)]:
        rows[8 + dy][w // 2 + dx] = c
    return rows


save(end(False), "m_sldlt.png")
save(rail(0, True), "m_sldmd1.png")
save(rail(1, False), "m_sldmd2.png")
save(end(True), "m_sldrt.png")
