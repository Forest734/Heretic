"""Render the views the screens are made from, with the engine under gdb.

usage: python3 render.py <crispy-heretic> <blasphem.wad> <shots dir>

Writes sbar.png (a frame showing the status bar), e2end.png, final1.png and
credit.png (views from the levels) as 320 x 200 images in the WAD's palette.
"""
import os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wad import Wad
from PIL import Image

ENGINE, WADFILE, OUT = (os.path.abspath(a) for a in sys.argv[1:4])

# name: (episode, map, x, y, angle in degrees, lookdir, z of the player's feet)
VIEWS = {
    "e2end": (2, 3, 3816, -90, 90, -25, 568),   # the river valley
    "final1": (3, 3, 80, 168, 196, 35, 60),     # the pentagram window
    "credit": (3, 5, -1192, 344, 0, -10, 144),  # the courtyard
}

def run(episode, level, gdb_lines, screenblocks):
    with tempfile.TemporaryDirectory() as d:
        open(f"{d}/heretic.cfg", "w").write(
            f"screenblocks {screenblocks}\nshow_messages 0\nusegamma 0\n")
        open(f"{d}/crispy-heretic.cfg", "w").write(
            "crispy_hires 0\ncrispy_widescreen 0\ncrispy_truecolor 0\n"
            "crispy_uncapped 0\ncrispy_crosshair 0\ncrispy_mouselook 1\n")
        open(f"{d}/x.gdb", "w").write("\n".join(
            ["set pagination off", "break P_Ticker if leveltime == 10", "run", "delete"]
            + gdb_lines + ["kill"]) + "\n")
        env = dict(os.environ, SDL_VIDEODRIVER="offscreen", SDL_AUDIODRIVER="dummy",
                   SDL_RENDER_DRIVER="software")
        subprocess.run(["gdb", "-q", "-batch", "-x", f"{d}/x.gdb", "--args", ENGINE,
                        "-iwad", WADFILE, "-warp", str(episode), str(level), "-skill", "3",
                        "-nomusic", "-nosound", "-nomonsters", "-window", "-geometry", "640x400",
                        "-config", f"{d}/heretic.cfg", "-extraconfig", f"{d}/crispy-heretic.cfg",
                        "-savedir", d], cwd=d, env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def to_palette(raw_path, png_path):
    """XRGB8888 frame to palette indices; the engine's gamma table shifts
    colours a little, so take the nearest."""
    pal = Wad(WADFILE).palette()
    raw = open(raw_path, "rb").read()
    cache, out = {}, bytearray()
    for i in range(0, len(raw), 4):
        c = (raw[i + 2], raw[i + 1], raw[i])
        if c not in cache:
            cache[c] = min(range(256), key=lambda k: sum((a - b) ** 2 for a, b in zip(pal[k], c)))
        out.append(cache[c])
    im = Image.frombytes("P", (320, 200), bytes(out))
    im.putpalette([b for c in pal for b in c])
    im.save(png_path)

os.makedirs(OUT, exist_ok=True)

for name, (ep, lv, x, y, ang, look, z) in VIEWS.items():
    run(ep, lv, [
        f"call P_TeleportMove(players[0].mo, {x} << 16, {y} << 16)",
        f"set var players[0].mo->angle = {int(ang % 360 / 360 * 2**32)}u",
        f"set var players[0].lookdir = {look}",
        f"set var players[0].mo->z = {z} << 16",
        "set var players[0].mo->flags = players[0].mo->flags | 0x200",  # MF_NOGRAVITY
        "set var players[0].psprites[0].state = 0",                      # no weapon
        "set var players[0].psprites[1].state = 0",
        "break I_FinishUpdate", "continue", "continue", "delete",
        "break SB_Drawer", "continue",                                   # before the HUD
        f"dump binary memory {OUT}/{name}.raw I_VideoBuffer I_VideoBuffer+64000",
    ], screenblocks=11)
    to_palette(f"{OUT}/{name}.raw", f"{OUT}/{name}.png")
    os.remove(f"{OUT}/{name}.raw")

# the status bar: three keys, full armour, three quartz flasks
run(1, 1, [
    "call P_GiveKey(&players[0], 0)", "call P_GiveKey(&players[0], 1)",
    "call P_GiveKey(&players[0], 2)", "call P_GiveArmor(&players[0], 1)",
    "call P_GiveArtifact(&players[0], 3, 0)", "call P_GiveArtifact(&players[0], 3, 0)",
    "call P_GiveArtifact(&players[0], 3, 0)", "call P_GiveArtifact(&players[0], 9, 0)",
    "call P_GiveArtifact(&players[0], 5, 0)",
    "set var players[0].health = 100", "set var players[0].mo->health = 100",
    "set var players[0].message = 0",
    "break I_FinishUpdate", "ignore $bpnum 60", "continue",  # let the counters settle
    f"dump binary memory {OUT}/sbar.raw I_VideoBuffer I_VideoBuffer+64000",
], screenblocks=10)
to_palette(f"{OUT}/sbar.raw", f"{OUT}/sbar.png")
os.remove(f"{OUT}/sbar.raw")
