"""Make the intermission maps Blasphemer left as placeholders.

usage: python3 make_maps.py <blasphem.wad> <graphics dir>

Writes, for wadinfo.txt and BlasphDM.txt:
  mape1.png, mape2.png, mape3.png  MAPE1-3  each episode's land, in ink on
                                            parchment, with a place for each
                                            level and roads between them
  in_x.png                         IN_X     the mark on a level that's done
  in_yah.png                       IN_YAH   the mark on the next one
The places are where in_lude.c's YAHspot puts the marks; the land is made
up around them from noise, the same every time.
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wad import Wad

wad = Wad(sys.argv[1]); out = sys.argv[2]
pal = np.array(wad.palette(), np.float32)
TRANSPARENT = (0, 47, 47)  # deutex's default

W, H, S = 320, 200, 4   # the screen, and how much finer it's drawn first

# in_lude.c's YAHspot: where the marks go, for maps 1-9 of episodes 1-3
YAH = [
    [(172, 78), (86, 90), (73, 66), (159, 95), (148, 126), (132, 54), (131, 74), (208, 138), (52, 101)],
    [(218, 57), (137, 81), (155, 124), (171, 68), (250, 86), (136, 98), (203, 90), (220, 140), (279, 106)],
    [(86, 99), (124, 103), (154, 79), (202, 83), (178, 59), (142, 58), (219, 66), (247, 57), (107, 80)],
]
# The marks are centred on the spots (IN_X's offsets are 4 4), and IN_YAH
# hangs above them.  The spots don't go in order across the land, so roads
# from each level to the next would cross all over; the roads join each
# place to its neighbours instead (a minimum spanning tree, which can't
# cross itself).

INK = (40, 25, 15)        # dark brown
RED_INK = (114, 30, 20)
PAPER = (198, 170, 134)

EPISODES = [
    # sea: the water's colour; land: the paper's tint there; trees and
    # mountains: how many; lava: the sea and rivers are lava; sites: what
    # stands at each level's spot
    dict(seed=11, sea=(150, 160, 146), sea_level=0.0, trees=0.55, mountains=0.6, rivers=2,
         lava=False, land=(1, 1, 1), sites=["docks", "crypt", "gate", "tower", "keep", "temple", "crypt", "maw", "graves"]),
    dict(seed=23, sea=(70, 16, 6), sea_level=0.02, trees=0.0, mountains=0.6, rivers=3,
         lava=True, land=(0.74, 0.68, 0.64), sites=["maw", "pits", "tower", "cave", "crypt", "keep", "temple", "gate", "cave"]),
    dict(seed=37, sea=(128, 128, 156), sea_level=0.0, trees=0.45, mountains=0.6, rivers=1,
         lava=False, land=(1, 1, 1), sites=["keep", "crypt", "tower", "keep", "cave", "temple", "gate", "castle", "tower"]),
]

# the screen coordinates of every fine pixel's centre
YY, XX = np.mgrid[0:H * S, 0:W * S].astype(np.float32)
XX = (XX + 0.5) / S; YY = (YY + 0.5) / S


def noise(rng, scale, octaves=4):
    """Fractal value noise over the screen, 0..1; scale is the coarsest
    feature in screen pixels."""
    acc = np.zeros((H * S, W * S), np.float32)
    amp = total = 0.0
    a = 1.0
    for o in range(octaves):
        gw = int(W / scale * 2 ** o) + 2
        gh = int(H / scale * 2 ** o) + 2
        g = rng.random((gh, gw)).astype(np.float32)
        acc += a * np.asarray(Image.fromarray(g).resize((W * S, H * S), Image.BICUBIC))
        total += a; a *= 0.5
    return acc / total


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def signed_distance(land):
    """Distance in screen pixels to the coast, + on land, from a fine mask;
    worked out at screen size and smoothed back up."""
    small = np.asarray(Image.fromarray(land.astype(np.float32)).resize((W, H), Image.BOX)) > 0.5
    edge = np.zeros_like(small)
    edge[:-1] |= small[:-1] != small[1:]; edge[1:] |= small[:-1] != small[1:]
    edge[:, :-1] |= small[:, :-1] != small[:, 1:]; edge[:, 1:] |= small[:, :-1] != small[:, 1:]
    pts = np.argwhere(edge).astype(np.float32) + 0.5
    gy, gx = np.mgrid[0:H, 0:W].astype(np.float32) + 0.5
    flat = np.stack([gy.ravel(), gx.ravel()], 1)
    best = np.full(len(flat), 1e9, np.float32)
    for i in range(0, len(pts), 512):
        p = pts[i:i + 512]
        d = ((flat[:, None, :] - p[None, :, :]) ** 2).sum(2)
        best = np.minimum(best, d.min(1))
    d = np.sqrt(best).reshape(H, W) * np.where(small, 1, -1)
    return np.asarray(Image.fromarray(d.astype(np.float32)).resize((W * S, H * S), Image.BICUBIC))


def line_cover(field, level, width):
    """How much of each fine pixel a line of the given width (screen pixels)
    along field == level covers; field is a distance in screen pixels."""
    return np.clip((width / 2 - np.abs(field - level)) * S + 0.5, 0, 1)


def mix(img, colour, cover):
    c = np.array(colour, np.float32)
    img += (c - img) * cover[..., None]


def make_map(ep):
    cfg = EPISODES[ep]
    rng = np.random.default_rng(cfg["seed"])
    spots = YAH[ep]

    # ---- the land: noise, raised around the places and lowered at the edges
    e = noise(rng, 90, 5) - 0.5
    for (sx, sy) in spots:
        e += 0.28 * np.exp(-((XX - sx) ** 2 + (YY - sy) ** 2) / (2 * 16 ** 2))
    edge = np.minimum(np.minimum(XX, W - XX), np.minimum(YY, H - YY) * 1.4)
    e -= 0.7 * (1 - smoothstep(0, 40, edge))
    land = e > cfg["sea_level"]
    d = signed_distance(land)

    # ---- the paper: mottled, stained and darker at the edges
    img = np.empty((H * S, W * S, 3), np.float32)
    img[:] = PAPER
    mott = noise(rng, 25, 5) - 0.5
    img *= (1 + 0.22 * mott)[..., None]
    stains = noise(rng, 60, 3)
    img *= (1 - 0.18 * smoothstep(0.55, 0.75, stains))[..., None]
    vign = smoothstep(0, 28, np.minimum(np.minimum(XX, W - XX), np.minimum(YY, H - YY)))
    img *= (0.62 + 0.38 * vign)[..., None]
    tint = 1 + (np.array(cfg["land"], np.float32) - 1) * smoothstep(-1, 3, d)[..., None]
    img *= tint

    # ---- the sea: a wash, with ripples drawn along the coast
    sea = smoothstep(0.0, -1.5, d)
    if cfg["lava"]:
        glow = smoothstep(-7, 0, d)
        lava = np.array(cfg["sea"], np.float32) * (1 + 0.25 * mott)[..., None]
        lava = lava + np.array([140, 70, 0], np.float32) * (glow ** 2)[..., None]
        img += (lava - img) * sea[..., None]
    else:
        wash = np.array(cfg["sea"], np.float32) * (1 + 0.15 * mott)[..., None]
        img += (wash - img) * (0.75 * sea)[..., None]
    for k, lvl in enumerate((-2.5, -5, -8.5, -13)):
        if cfg["lava"]:
            mix(img, (250, 150, 30), line_cover(d, lvl, 0.5) * (0.4 - 0.1 * k))
        else:
            mix(img, INK, line_cover(d, lvl, 0.55) * (0.55 - 0.1 * k))

    # ---- the coast
    mix(img, INK, line_cover(d, 0, 1.1))

    pic = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(pic)
    drawer = Drawer(draw)

    # ---- the compass goes in whichever corner has the most open sea
    corners = [(282, 166), (38, 166), (282, 52), (38, 52)]
    def openness(c):
        cx, cy = c
        m = (XX - cx) ** 2 + (YY - cy) ** 2 < 18 ** 2
        return np.mean(d[m] < -2)
    compass = max(corners, key=openness)

    # ---- rivers, from high ground down to the sea
    ry, rx = np.gradient(d)
    taken = [(sx, sy, 13) for sx, sy in spots]
    for _ in range(cfg["rivers"]):
        river = trace_river(rng, d, rx, ry, spots)
        if river:
            colour = (230, 90, 10) if cfg["lava"] else tuple(int(c * 0.8) for c in cfg["sea"])
            drawer.river(river, colour)

    # ---- mountains and trees, back to front, kept off the places, the
    # roads, the name at the top and the compass
    roads = spanning_tree(spots)
    clear = [(x, y, 6) for x, y in road_points(spots, roads, rng)] + taken + [compass + (22,)]
    things = []
    hill = noise(rng, 40, 3)
    wood = noise(rng, 30, 3)
    for gy in range(46, H - 10, 7):
        for gx in range(10, W - 10, 8):
            x = gx + rng.uniform(-3, 3); y = gy + rng.uniform(-3, 3)
            ix, iy = int(x * S), int(y * S)
            if d[iy, ix] < 4 or any((x - cx) ** 2 + (y - cy) ** 2 < r * r for cx, cy, r in clear):
                continue
            if hill[iy, ix] > 1 - 0.5 * cfg["mountains"] and d[iy, ix] > 7:
                things.append((y, "volcano" if cfg["lava"] and rng.random() < 0.3 else "mountain", x))
            elif wood[iy, ix] > 1 - 0.5 * cfg["trees"]:
                for t in range(3):
                    tx, ty = x + rng.uniform(-4, 4), y + rng.uniform(-3, 3)
                    if d[int(ty * S), int(tx * S)] > 2:
                        things.append((ty, "tree", tx))
    for y, kind, x in sorted(things):
        getattr(drawer, kind)(x, y, rng)

    # ---- roads, then the places
    drawer.roads(spots, roads, rng)
    for (sx, sy), kind in zip(spots, cfg["sites"]):
        getattr(drawer, "site_" + kind)(sx, sy)

    # ---- a compass, and a frame
    drawer.compass(*compass, ink=(235, 170, 70) if cfg["lava"] else INK)
    for inset, wdt in ((3, 1.0), (5.5, 0.5)):
        drawer.rect(inset, inset, W - inset, H - inset, wdt)

    small = pic.resize((W, H), Image.BOX)
    return quantise(np.asarray(small).astype(np.float32), dither=True)


def trace_river(rng, d, rx, ry, spots):
    """A river from a high place down the slope of the coast distance, which
    always leads to the sea, wandering a little."""
    best = None
    for _ in range(200):
        x, y = rng.uniform(20, W - 20), rng.uniform(50, H - 20)
        dd = d[int(y * S), int(x * S)]
        if dd > 10 and all((x - sx) ** 2 + (y - sy) ** 2 > 400 for sx, sy in spots):
            best = (x, y); break
    if not best:
        return None
    x, y = best
    pts = [(x, y)]
    ang = rng.uniform(0, 2 * math.pi)
    for step in range(400):
        ix, iy = min(W * S - 1, int(x * S)), min(H * S - 1, int(y * S))
        gx, gy = -rx[iy, ix], -ry[iy, ix]
        n = math.hypot(gx, gy) or 1
        ang += rng.normal(0, 0.35)
        dx = gx / n + 0.6 * math.cos(ang); dy = gy / n + 0.6 * math.sin(ang)
        n = math.hypot(dx, dy) or 1
        x += dx / n; y += dy / n
        pts.append((x, y))
        if not (2 < x < W - 2 and 2 < y < H - 2) or d[min(H * S - 1, int(y * S)), min(W * S - 1, int(x * S))] < -1:
            break
    return pts if len(pts) > 15 else None


def bezier(p0, p2, bend):
    (x0, y0), (x2, y2) = p0, p2
    mx, my = (x0 + x2) / 2, (y0 + y2) / 2
    nx, ny = -(y2 - y0), x2 - x0
    x1, y1 = mx + nx * bend, my + ny * bend
    n = int(math.hypot(x2 - x0, y2 - y0) * 3) + 2
    return [((1 - t) ** 2 * x0 + 2 * (1 - t) * t * x1 + t * t * x2,
             (1 - t) ** 2 * y0 + 2 * (1 - t) * t * y1 + t * t * y2)
            for t in (i / n for i in range(n + 1))]


ROAD_BENDS = {}


def spanning_tree(spots):
    """Prim's: the shortest roads that join every place, as (a, b) pairs of
    map numbers."""
    done = {0}
    roads = []
    while len(done) < len(spots):
        a, b = min(((a, b) for a in done for b in range(len(spots)) if b not in done),
                   key=lambda ab: math.dist(spots[ab[0]], spots[ab[1]]))
        done.add(b); roads.append((a + 1, b + 1))
    return roads


def road_points(spots, roads, rng):
    pts = []
    for a, b in roads:
        bend = ROAD_BENDS.setdefault((tuple(spots[a - 1]), tuple(spots[b - 1])), rng.uniform(-0.12, 0.12))
        pts += bezier(spots[a - 1], spots[b - 1], bend)[::3]
    return pts


class Drawer:
    """Ink drawing in screen coordinates on the fine picture."""

    def __init__(self, draw):
        self.d = draw

    def P(self, pts):
        return [(x * S, y * S) for x, y in pts]

    def line(self, pts, colour=INK, width=1.0):
        self.d.line(self.P(pts), fill=colour, width=max(1, round(width * S)), joint="curve")

    def poly(self, pts, fill=None, outline=INK, width=1.0):
        if fill:
            self.d.polygon(self.P(pts), fill=fill)
        if outline:
            self.line(pts + [pts[0]], outline, width)

    def rect(self, x0, y0, x1, y1, width=1.0, fill=None):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill=fill, width=width)

    def dot(self, x, y, r, colour):
        self.d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=colour)

    # -- land
    def river(self, pts, colour):
        for i in range(len(pts) - 1):
            w = 0.6 + 1.2 * i / len(pts)
            self.line(pts[i:i + 2], colour, w + 0.7)
        for i in range(len(pts) - 1):
            w = 0.6 + 1.2 * i / len(pts)
            self.line(pts[i:i + 2], tuple(min(255, int(c * 1.15)) for c in colour), max(0.3, w - 0.4))

    def mountain(self, x, y, rng):
        w = rng.uniform(7, 11); h = w * rng.uniform(0.6, 0.85)
        px = x + rng.uniform(-1, 1)
        shape = [(x - w / 2, y), (px, y - h), (x + w / 2, y)]
        self.poly(shape, fill=PAPER, outline=None)
        # the shaded side, hatched
        for k in range(1, 5):
            t = k / 5
            self.line([(px + (x + w / 2 - px) * t, y - h + h * t), (px + (x + w / 2 - px) * t * 0.35, y)],
                      INK, 0.4)
        self.line(shape, INK, 0.9)

    def volcano(self, x, y, rng):
        w = rng.uniform(10, 13); h = w * 0.62
        shape = [(x - w / 2, y), (x - 1.8, y - h), (x + 1.8, y - h), (x + w / 2, y)]
        self.poly(shape, fill=(150, 128, 104), outline=None)
        for k in range(1, 4):
            t = k / 4
            self.line([(x + 1.8 + (w / 2 - 1.8) * t, y - h + h * t), (x + 1.8 + (w / 2 - 1.8) * t * 0.3, y)],
                      INK, 0.4)
        # lava from the crater, down the lit side
        self.line([(x - 0.8, y - h), (x - 1.8, y - h * 0.55), (x - 1.2, y - h * 0.2)], (235, 100, 10), 0.8)
        self.line(shape, INK, 0.9)
        self.d.ellipse([(x - 1.8) * S, (y - h - 0.7) * S, (x + 1.8) * S, (y - h + 0.7) * S],
                       fill=(250, 150, 20), outline=INK, width=max(1, round(0.4 * S)))
        for k in range(3):   # smoke, drifting
            r = 1.0 + 0.4 * k
            cx, cy = x + 0.8 + 1.3 * k, y - h - 2.2 - 2.3 * k
            self.d.ellipse([(cx - r) * S, (cy - r * 0.8) * S, (cx + r) * S, (cy + r * 0.8) * S],
                           fill=(120, 108, 100), outline=(70, 60, 55), width=max(1, round(0.3 * S)))

    def tree(self, x, y, rng):
        r = rng.uniform(1.4, 2.0)
        self.line([(x, y), (x, y - r)], INK, 0.5)
        self.d.ellipse([(x - r) * S, (y - r * 2.6) * S, (x + r) * S, (y - r * 0.6) * S],
                       fill=(101, 111, 88), outline=INK, width=max(1, round(0.5 * S)))

    # -- roads: dots of red ink, a little bent
    def roads(self, spots, roads, rng):
        for a, b in roads:
            p0, p1 = spots[a - 1], spots[b - 1]
            bend = ROAD_BENDS[(tuple(p0), tuple(p1))]
            pts = bezier(p0, p1, bend)
            acc = 0
            last = pts[0]
            for p in pts[1:]:
                acc += math.hypot(p[0] - last[0], p[1] - last[1]); last = p
                near = min(math.hypot(p[0] - q[0], p[1] - q[1]) for q in (p0, p1))
                if near < 8:
                    continue
                if acc >= 3.0:
                    acc = 0
                    self.dot(p[0], p[1], 0.75, RED_INK)

    # -- places: about 14 x 14, standing on the spot
    def ground(self, x, y, w=8):
        self.d.ellipse([(x - w) * S, (y + 2) * S, (x + w) * S, (y + 6) * S], fill=PAPER)
        self.line([(x - w + 1, y + 4), (x + w - 1, y + 4)], INK, 0.6)

    def roof(self, x0, x1, y, h, colour=RED_INK):
        self.poly([(x0, y), ((x0 + x1) / 2, y - h), (x1, y)], fill=colour, width=0.6)

    def site_keep(self, x, y):
        self.ground(x, y)
        self.rect(x - 4, y - 5, x + 4, y + 4, 0.8, fill=PAPER)
        for i in range(4):
            self.rect(x - 4 + i * 2.2, y - 7, x - 3 + i * 2.2, y - 5, 0.6, fill=PAPER)
        self.rect(x - 1, y + 1, x + 1, y + 4, 0.6, fill=INK)
        self.dot(x - 2, y - 2, 0.5, INK); self.dot(x + 2, y - 2, 0.5, INK)

    def site_castle(self, x, y):
        self.ground(x, y, 9)
        self.rect(x - 6, y - 2, x + 6, y + 4, 0.8, fill=PAPER)
        for tx in (x - 7, x + 4):
            self.rect(tx, y - 6, tx + 3, y + 4, 0.8, fill=PAPER)
            self.roof(tx - 0.5, tx + 3.5, y - 6, 4)
        self.rect(x - 1.2, y + 1, x + 1.2, y + 4, 0.6, fill=INK)

    def site_tower(self, x, y):
        self.ground(x, y, 6)
        self.rect(x - 2.5, y - 6, x + 2.5, y + 4, 0.8, fill=PAPER)
        self.roof(x - 3.5, x + 3.5, y - 6, 5)
        self.dot(x, y - 3, 0.6, INK)

    def site_gate(self, x, y):
        self.ground(x, y, 9)
        for tx in (x - 7, x + 3):
            self.rect(tx, y - 5, tx + 4, y + 4, 0.8, fill=PAPER)
            for i in range(2):
                self.rect(tx + i * 2.4, y - 7, tx + 1.4 + i * 2.4, y - 5, 0.5, fill=PAPER)
        self.rect(x - 3, y - 3, x + 3, y + 4, 0.8, fill=PAPER)
        self.d.chord([(x - 2) * S, (y - 1) * S, (x + 2) * S, (y + 3) * S], 180, 360, fill=INK)
        self.rect(x - 2, y + 1, x + 2, y + 4, 0.1, fill=INK)

    def site_temple(self, x, y):
        self.ground(x, y, 8)
        self.rect(x - 5, y - 1, x + 6, y + 4, 0.8, fill=PAPER)
        self.roof(x - 5.5, x + 6.5, y - 1, 3.5)
        self.rect(x - 6, y - 5, x - 3, y + 4, 0.8, fill=PAPER)
        self.roof(x - 6.5, x - 2.5, y - 5, 6)
        self.dot(x + 1, y + 1.5, 0.7, INK)

    def site_crypt(self, x, y):
        self.ground(x, y, 7)
        self.rect(x - 4, y - 1, x + 4, y + 4, 0.8, fill=PAPER)
        self.roof(x - 5, x + 5, y - 1, 3, PAPER)
        self.rect(x - 1, y + 1, x + 1, y + 4, 0.5, fill=INK)
        self.line([(x, y - 4), (x, y - 8)], INK, 0.8)
        self.line([(x - 1.5, y - 6.5), (x + 1.5, y - 6.5)], INK, 0.8)

    def site_graves(self, x, y):
        self.ground(x, y, 8)
        for gx, gy in ((-5, 1), (0, -1), (5, 1), (-2.5, 3.5), (2.5, 3.5)):
            self.line([(x + gx, y + gy - 3), (x + gx, y + gy + 1)], INK, 0.7)
            self.line([(x + gx - 1.3, y + gy - 1.8), (x + gx + 1.3, y + gy - 1.8)], INK, 0.7)

    def site_cave(self, x, y):
        self.poly([(x - 8, y + 4), (x - 4, y - 5), (x + 1, y - 7), (x + 6, y - 3), (x + 8, y + 4)],
                  fill=PAPER, width=0.8)
        self.d.chord([(x - 3) * S, (y - 2) * S, (x + 3) * S, (y + 8) * S], 180, 360, fill=INK)
        self.line([(x - 8, y + 4), (x + 8, y + 4)], INK, 0.8)

    def site_maw(self, x, y):
        self.site_cave(x, y)
        for i in range(4):   # teeth
            tx = x - 2.2 + i * 1.5
            self.poly([(tx, y + 0.5), (tx + 0.7, y + 2.2), (tx + 1.4, y + 0.5)], fill=PAPER, outline=None)
        self.dot(x - 1.5, y - 3.8, 0.55, (200, 20, 10)); self.dot(x + 1.5, y - 3.8, 0.55, (200, 20, 10))

    def site_pits(self, x, y):
        self.ground(x, y, 8)
        for gx, gy in ((-4, 0), (3, -1), (0, 3)):
            self.d.ellipse([(x + gx - 2.5) * S, (y + gy - 1.2) * S, (x + gx + 2.5) * S, (y + gy + 1.2) * S],
                           fill=(220, 80, 10), outline=INK, width=max(1, round(0.6 * S)))

    def site_docks(self, x, y):
        self.ground(x, y, 8)
        self.rect(x - 5, y - 3, x + 1, y + 3, 0.8, fill=PAPER)
        self.roof(x - 6, x + 2, y - 3, 3.5)
        for k in range(3):
            self.line([(x + 2, y + 1 + k * 1.5), (x + 8, y + 1 + k * 1.5)], INK, 0.5)
        self.line([(x + 6, y - 6), (x + 6, y + 1)], INK, 0.6)    # a mast
        self.poly([(x + 6.3, y - 5.5), (x + 9, y - 1.5), (x + 6.3, y - 1.5)], fill=PAPER, width=0.5)

    def compass(self, x, y, ink):
        """Drawn in gold on the lava, where dark ink wouldn't show."""
        r = 12
        paper = PAPER if ink == INK else (70, 16, 6)
        self.d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], outline=ink, width=max(1, round(0.7 * S)))
        self.d.ellipse([(x - r + 2) * S, (y - r + 2) * S, (x + r - 2) * S, (y + r - 2) * S], outline=ink,
                       width=max(1, round(0.4 * S)))
        for k in range(8):
            a = k * math.pi / 4 - math.pi / 2
            rr = r + 3 if k % 2 == 0 else r - 3
            tip = (x + rr * math.cos(a), y + rr * math.sin(a))
            side = 2.6 if k % 2 == 0 else 1.8
            l = (x + side * math.cos(a - math.pi / 2), y + side * math.sin(a - math.pi / 2))
            rgt = (x + side * math.cos(a + math.pi / 2), y + side * math.sin(a + math.pi / 2))
            self.poly([l, tip, (x, y)], fill=ink if k % 2 == 0 else paper, outline=ink, width=0.5)
            self.poly([(x, y), tip, rgt], fill=paper if k % 2 == 0 else ink, outline=ink, width=0.5)
        # N
        nx, ny = x, y - r - 7
        self.line([(nx - 1.5, ny + 2), (nx - 1.5, ny - 2), (nx + 1.5, ny + 2), (nx + 1.5, ny - 2)], ink, 0.7)


# ---- palette: the browns, reds, oranges and the greys and blues the washes
# need; dithered so the paper's shading doesn't band
KEEP = list(range(0, 8)) + list(range(36, 52)) + list(range(52, 68)) + list(range(72, 111)) \
    + list(range(111, 160)) + list(range(169, 180)) + list(range(224, 247))
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - 0.47


def quantise(rgb, dither):
    h, w, _ = rgb.shape
    if dither:
        rgb = rgb + (np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w] * 10)[..., None]
    keep = np.array(KEEP)
    p = pal[keep]
    flat = rgb.reshape(-1, 3)
    wgt = np.array([0.30, 0.59, 0.11], np.float32) * 3
    best = np.zeros(len(flat), np.int64)
    bestd = np.full(len(flat), 1e18, np.float32)
    for i, c in enumerate(p):
        dd = (((flat - c) ** 2) * wgt).sum(1)
        m = dd < bestd
        bestd[m] = dd[m]; best[m] = keep[i]
    return best.reshape(h, w)


def save(idx, name, mask=None):
    rgb = pal[idx].astype(np.uint8)
    if mask is not None:
        rgb[~mask] = TRANSPARENT
    Image.fromarray(rgb).save(os.path.join(out, name))


# ---- IN_X and IN_YAH, drawn pixel by pixel
def mark_x():
    """A 9 x 9 cross of red ink, a broad stroke down and a thin one across,
    outlined; offsets 4 4 centre it."""
    n = 9
    idx = np.zeros((n, n), np.int64); m = np.zeros((n, n), bool)
    for y in range(n):
        for x in range(n):
            broad = abs(x - y) <= 1 and 0 < x < n - 1 and 0 < y < n - 1
            if x == y or broad or x + y == n - 1:
                m[y, x] = True; idx[y, x] = 152 if (x + y) % 3 else 155
    out_m = m.copy()
    for y in range(n):
        for x in range(n):
            if not m[y, x] and any(0 <= y + dy < n and 0 <= x + dx < n and m[y + dy, x + dx]
                                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out_m[y, x] = True; idx[y, x] = 72
    return idx, out_m


def mark_yah():
    """A gold arrow pointing down, outlined; offsets 4 21 put its point
    above the place on the spot."""
    rows = ["...###...",
            "...#o#...",
            "...#o#...",
            "...#o#...",
            "...#o#...",
            "#####o###",
            ".#ooooo#.",
            "..#ooo#..",
            "...#o#...",
            "....#...."]
    h, w = len(rows), len(rows[0])
    idx = np.zeros((h, w), np.int64); m = np.zeros((h, w), bool)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == "#":
                idx[y, x] = 72; m[y, x] = True
            elif ch == "o":
                idx[y, x] = 143 if x < w // 2 or y < 5 else 141; m[y, x] = True
    return idx, m


if __name__ == "__main__":
    for ep in range(3):
        save(make_map(ep), f"mape{ep + 1}.png")
    i, m = mark_x(); save(i, "in_x.png", m)
    i, m = mark_yah(); save(i, "in_yah.png", m)
