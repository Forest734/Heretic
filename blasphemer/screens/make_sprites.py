"""Make the sprites Blasphemer left as placeholders, from its own art.

usage: python3 make_sprites.py <blasphem.wad> <sprites dir>

From the WAD, in its palette, writes for wadinfo.txt and BlasphDM.txt:
  amp1a0.png ... amp1c0.png  AMP1A0-C0  Flame Tooth and Flame Jaws, the
  amp2a0.png ... amp2c0.png  AMP2A0-C0  Phoenix Rod's ammo, in fire colours
Offsets go in wadinfo.txt.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wad import Wad
from PIL import Image

wad = Wad(sys.argv[1]); out = sys.argv[2]
pal = wad.palette()
TRANSPARENT = (0, 47, 47)  # deutex's default


def save(rows, name):
    """rows: lists of palette indices, None where transparent."""
    h, w = len(rows), len(rows[0])
    im = Image.new("RGB", (w, h))
    im.putdata([TRANSPARENT if c is None else pal[c] for r in rows for c in r])
    im.save(os.path.join(out, name))


# ---- AMP1A0-C0 and AMP2A0-C0: Blasphemer's were the Frostfang's Ice Shard
# and Ice Jewel (AMB1, AMB2) with their blues swapped for greens.  These
# swap them for fire instead, shade for shade: its blues run dark to light
# from 190 to 208, and go to deep red, orange and yellow.  The fire is all
# within r_bmaps.c's bl_fire, so the brightmap lights it and not the silver.
FIRE = [149, 152, 137, 138, 139, 140, 244, 243, 242, 241, 143, 144]


def fire(c):
    if c is None or not 185 <= c <= 208:
        return c
    t = max(0, c - 190) / (208 - 190)
    return FIRE[round(t * (len(FIRE) - 1))]


for ice, flame in (("AMB1", "amp1"), ("AMB2", "amp2")):
    for frame in "abc":
        _, _, _, _, rows = wad.patch(f"{ice}{frame}0")
        save([[fire(c) for c in row] for row in rows], f"{flame}{frame}0.png")
