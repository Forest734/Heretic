"""Compose Blasphemer's help, credit and ending screens.

usage: python3 make_screens.py <blasphem.wad> <shots dir> <lumps dir>

The WAD gives the palette, fonts, icons and flats; the shots dir holds what
render.py made. Writes, for wadinfo.txt and BlasphDM.txt:
  helpbar.png   HELP1   the status bar and the artifacts
  helpkeys.png  HELP2   the controls
  credits.png   CREDIT
  e2vista.png   E2END   shown after episode 2, with E2PAL
  e3window.png  FINAL1  shown after episode 3, then scrolls down ...
  e3stars.png   FINAL2  ... to bring this in from above
  e2pal.lmp     E2PAL   the game's own palette, so E2END needs no other
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wad import Wad
from compose import Screen, W, H
from PIL import Image

wad = Wad(sys.argv[1]); shots = sys.argv[2]; out = sys.argv[3]
os.makedirs(out, exist_ok=True)
shot = lambda n: Image.open(os.path.join(shots, n))

def colours(s):
    """Gold for headings, off-white for text."""
    return s.ramp((255, 190, 90)), s.ramp((235, 230, 220))

# ---- HELP1: the status bar and the artifacts
s = Screen(wad); gold, white = colours(s)
s.flat("FLOOR04", light=12)
s.text("THE STATUS BAR", 0, 3, big=True, remap=gold, center=True)
bar = shot("sbar.png").crop((0, 158, 320, 200))
top = 22
s.box(0, top - 1, W, top + 43, s.black)
s.image(bar, 0, top)
def label(text, x, xfield, yfield):
    """Label under the bar at x (centre), with a line up to the field."""
    y = top + 46
    s.text(text, x, y, remap=gold, center=x)
    lx = xfield if abs(xfield - x) < s.text_width(text) // 2 else x
    for yy in range(top + yfield, y - 1):
        s.put(lx, yy, gold[200] if yy % 2 else s.black)
label("AMMO", 112, 121, 30)
label("KEYS", 160, 158, 30)
label("ARTIFACT", 205, 196, 33)
label("LIFE GEM", 277, 277, 37)
s.text("ARTIFACTS", 0, 79, big=True, remap=gold, center=True)
rows = [[("ARTIPTN2", "QUARTZ FLASK"), ("ARTIINVU", "RING OF INVINCIBILITY"),
         ("ARTITRCH", "TORCH"), ("ARTIINVS", "SHADOWSPHERE"), ("ARTISOAR", "WINGS OF WRATH")],
        [("ARTIPWBK", "TOME OF POWER"), ("ARTIFBMB", "TIME BOMB OF THE ANCIENTS"),
         ("ARTIEGGC", "MORPH OVUM"), ("ARTISPHL", "MYSTIC URN"), ("ARTIATLP", "CHAOS DEVICE")]]
split = {"RING OF INVINCIBILITY": ["RING OF", "INVINCIBILITY"],
         "TIME BOMB OF THE ANCIENTS": ["TIME BOMB OF", "THE ANCIENTS"],
         "SHADOWSPHERE": ["SHADOW-", "SPHERE"]}
for r, row in enumerate(rows):
    base = (127, 175)[r]     # icons stand on this line, names below it
    for c, (icon, name) in enumerate(row):
        cx = (30, 100, 166, 226, 286)[c]  # the wide names get room
        w, h = s.patch_size(icon)
        s.patch(icon, cx - w // 2, base - h, offsets=False)
        words = name.split()
        lines = split.get(name, [" ".join(words[:len(words) // 2]), " ".join(words[len(words) // 2:])]
                          if len(words) > 1 else [name])
        for i, line in enumerate(lines):
            s.text(line, 0, base + 3 + i * 9, remap=white, center=cx)
s.save(f"{out}/helpbar.png")

# ---- HELP2: the controls
s = Screen(wad); gold, white = colours(s)
s.flat("FLOOR04", light=12)
s.text("CONTROLS", 0, 3, big=True, remap=gold, center=True)
controls = [
    ("MOVE", "W  S   OR   UP  DOWN"),
    ("STRAFE", "A  D"),
    ("TURN", "LEFT  RIGHT   OR   MOUSE"),
    ("FIRE", "CTRL   OR   LEFT BUTTON"),
    ("OPEN / USE", "SPACE"),
    ("RUN", "SHIFT     ALWAYS RUN  CAPS LOCK"),
    ("SIDESTEP", "HOLD ALT AND TURN"),
    ("JUMP", "/     WHEN TURNED ON IN CRISPNESS"),
    ("WEAPONS", "1 TO 8"),
    ("LOOK UP / DOWN", "PGDN  DEL     CENTRE  END"),
    ("FLY UP / DOWN", "PGUP  INS     LAND  HOME"),
    ("ARTIFACTS", "[  ]  CHOOSE     ENTER  USE"),
    ("TOME OF POWER", "BACKSPACE"),
    ("MAP", "TAB"),
    ("SAVE / LOAD", "F2  F3     QUICK  F6  F9"),
    ("MENU", "ESC     BRIGHTNESS  F11"),
]
y = 27
for what, keys in controls:
    s.text(what, 16, y, remap=gold)
    s.text(keys, 118, y, remap=white)
    y += 10
s.save(f"{out}/helpkeys.png")

# ---- CREDIT
s = Screen(wad); gold, white = colours(s)
s.image(shot("credit.png"))
s.darken(21)
s.text("CREDITS", 0, 3, big=True, remap=gold, center=True)
credits = [
    ("PROJECT", 'SPRINGY  CACOWAD  G. "STILGAR" WESSNER  JUTE GYTE  SODAHOLIC'),
    ("LEVELS", 'JUTE GYTE  CACOWAD  SNARBOO  RYATHAEN  OWEN "SARGE BALDY" LLOYD  SUPORMA  CRANEO  ETTINGRINDER  RELLIK  HELLBENT'),
    ("GRAPHICS", 'STILGAR  SODAHOLIC  DOOMAD  BLOX  ERIANCE  WARFARE  LEILEI  ESSELFORTIUM  MECHADON  40OZ  ESPI  AIRRAID  MELLOW  FREDRIK  PAWEL "NMN" ZARCZYNSKI  NEOWORM  PRINTZ  CLEBARDMAN  CATOPTROMANCY  BETHOFDEATH  LOKITO  LINGUICA  BIGPROJECTALONE  HORRORMOVIEGUY'),
    ("MUSIC AND SOUND", "JUTE GYTE  SODAHOLIC  ARTISTICDUDE"),
    ("DATA AND FIXES", "LEILEI  GREYGHOST  SKIBBI  CATOPTROMANCY"),
    ("ENGINE", "CRISPY DOOM  FABIAN GREFFRATH     CHOCOLATE DOOM  SIMON HOWARD     HERETIC SOURCE  RAVEN SOFTWARE"),
]
y, left, right = 28, 8, 314
for head, names in credits:
    hx = s.text(head + ":", left, y, remap=gold) + 4
    # names are separated by two spaces; keep each name whole
    items = [n.strip() for n in names.split("  ") if n.strip()]
    x = hx
    for n in items:
        wn = s.text_width(n)
        if x + wn > right:
            y += 9; x = left + 12
        s.text(n, x, y, remap=white)
        x += wn + 8
    y += 11
assert y <= H, f"the credits run off the screen (y = {y})"
s.save(f"{out}/credits.png")

# ---- E2END and FINAL1: rendered views
s = Screen(wad); s.image(shot("e2end.png")); s.save(f"{out}/e2vista.png")
f1 = Screen(wad); f1.image(shot("final1.png")); f1.save(f"{out}/e3window.png")

# ---- FINAL2: the sky above FINAL1, which the scroll pans up into
s = Screen(wad)
band = 64  # FINAL1's top rows are open sky
tile = [bytes(f1.px[y * W:(y + 1) * W]) for y in range(band)]
for y in range(H):
    # Fill upwards from the bottom row, which sits just above FINAL1's top,
    # with copies of that band; every other copy is turned upside down and
    # mirrored so the stars don't visibly repeat.
    k = H - 1 - y
    n, r = divmod(k, band)
    src = tile[band - 1 - r] if n % 2 == 0 else tile[r]
    if n % 2:
        src = src[::-1]
    s.px[y * W:(y + 1) * W] = src
s.patch("M_HTIC", (W - 142) // 2, 46, offsets=False)
s.text("THE END", 0, 116, big=True, remap=gold, center=True)
s.save(f"{out}/e3stars.png")

# ---- E2PAL: E2END is drawn in the game's own palette
open(f"{out}/e2pal.lmp", "wb").write(wad.lump("PLAYPAL")[:768])
