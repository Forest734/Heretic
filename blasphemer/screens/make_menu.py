"""Make the menu and status bar graphics Blasphemer left as placeholders.

usage: python3 make_menu.py <blasphem.wad> <graphics dir>

From the WAD's own art, in its palette, writes for wadinfo.txt and BlasphDM.txt:
  m_skl00.png ... m_skl17.png  M_SKL00-17  the medallion spinning beside
                                            the main menu's title (PSKULL)
  m_fslot.png                  M_FSLOT     a save slot, cut into the status
                                            bar's stone (BARBACK)
  m_sldlt.png, m_sldmd1.png,   M_SLDLT ... the slider's ends and rail, in the
  m_sldmd2.png, m_sldrt.png    M_SLDRT     menu font's silver
  invgeml1.png ... invgemr2.png INVGEML1 .. blue gems pointing left and right,
                                INVGEMR2    lit and dim, for the inventory bar
                                            and the Crispness menu's cursor
  useartia.png ... useartie.png USEARTIA-E  the flash in the artifact box when
                                            an artifact is used
  lame.png                     LAME        a deathmatch frag count below -9
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


# ---- INVGEML1/2 and INVGEMR1/2: the inventory bar blinks them at the top of
# its ends, between the lit (1) and the dim (2), when there are more
# artifacts that way, and the Crispness menu blinks INVGEMR1/2 beside an
# item as its cursor, 14 pixels left of the text and a pixel above it.  So:
# 7 x 9, no offsets, in the slider knob's blues.
def gem(right, lit):
    h, w = 9, 7
    rows = [[None] * w for _ in range(h)]
    for y in range(h):
        reach = round(6 - abs(y - 4) * 1.5)   # the point is on the middle row
        for x in range(reach + 1):
            rows[y][x] = 0
    shift = 0 if lit else -5
    for y in range(h):
        for x in range(w):
            if rows[y][x] is None:
                continue
            edge = any(not (0 <= y + dy < h and 0 <= x + dx < w) or rows[y + dy][x + dx] is None
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if edge:
                rows[y][x] = 185                                 # the darkest blue
            else:
                rows[y][x] = (199 if y < 4 else 194 if y == 4 else 190) + shift
    rows[2][1] = 205 + shift                                     # a glint
    if not right:
        rows = [list(reversed(r)) for r in rows]
    return rows


for side, right in (("l", False), ("r", True)):
    save(gem(right, True), f"invgem{side}1.png")
    save(gem(right, False), f"invgem{side}2.png")


# ---- USEARTIA-E: using an artifact sets ArtifactFlash to 4, and the status
# bar shows USEARTI(A + flash - 1) for a tic each, so D, C, B, then A (E is
# never shown), over BLACKSQ in the artifact box at (182, 161), or over the
# view in the full-screen HUD.  A burst of fire from the box's middle, at
# its brightest first, then fading as it spreads.  30 x 30 with offsets 4 1
# fills BLACKSQ's square.
FIRE = [(0.90, 35), (0.75, 144), (0.62, 241), (0.50, 242), (0.40, 243), (0.31, 245), (0.23, 246)]


def burst(strength):
    n, ss = 30, 4
    radius = 5 + 9 * (1 - strength)
    rows = []
    for y in range(n):
        row = []
        for x in range(n):
            total = 0.0
            for sy in range(ss):
                for sx in range(ss):
                    dx = x + (sx + 0.5) / ss - n / 2
                    dy = y + (sy + 0.5) / ss - n / 2
                    r = math.hypot(dx, dy)
                    a = math.atan2(dy, dx)
                    rays = max(0.0, math.cos(4 * a)) ** 6 + 0.6 * max(0.0, math.cos(4 * a + math.pi)) ** 10
                    ring = math.exp(-((r - radius) / 2.2) ** 2)
                    core = math.exp(-(r / (radius * 0.55)) ** 2)
                    total += strength * (core + 0.55 * ring + 0.7 * rays * math.exp(-r / (radius * 0.9)))
            v = total / (ss * ss)
            row.append(next((c for t, c in FIRE if v >= t), None))
        rows.append(row)
    return rows


for i, letter in enumerate("abcde"):
    save(burst(0.35 + 0.65 * i / 4), f"usearti{letter}.png")


# ---- LAME: DrINumber shows it, at (x + 1, y + 1), for a number below -9,
# where the three digits would go; only a deathmatch frag count gets there,
# as health is shown no lower than 0.  In the status bar digits' blocky reds.
LETTERS = {
    "L": ["oo....", "oo....", "oo....", "oo....", "oo....", "oo....", "oooooo", "oooooo"],
    "A": [".oooo.", "oooooo", "oo..oo", "oo..oo", "oooooo", "oooooo", "oo..oo", "oo..oo"],
    "M": ["oo...oo", "ooo.ooo", "ooooooo", "oo.o.oo", "oo...oo", "oo...oo", "oo...oo", "oo...oo"],
    "E": ["oooooo", "oooooo", "oo....", "ooooo.", "ooooo.", "oo....", "oooooo", "oooooo"],
}
SHADE = [156, 156, 154, 154, 153, 153, 148, 145]   # lit from above, as IN0-9
lame = [[] for _ in range(8)]
for k, ch in enumerate("LAME"):
    for y in range(8):
        lame[y] += [SHADE[y] if c == "o" else None for c in LETTERS[ch][y]] + ([None] if k < 3 else [])
save(lame, "lame.png")
