"""Blasphemer's own names for its weapons, ammo, artifacts, armour, skill
levels and maps, as the game shows them.

usage: python3 names.py <src/heretic/deh_htext.c> <lumps dir>

Blasphemer named most of its things in lumps/language.lmp, which only
ZDoom-style ports read, and its maps in its CHANGELOG.md and commit messages.
This writes them as hehacked.lmp, the HEHACKED lump: an HHE patch in the WAD,
which crispy-heretic loads by itself. HHE replaces a string by its offset in
heretic.exe, so the offsets are looked up in the engine's own table. They're
Heretic 1.0's, which the engine assumes unless told otherwise (-hhever); 1.0
had no episodes 4 and 5, so their maps keep Heretic's names. In Blasphemer
those are deathmatch maps and placeholders.

make_screens.py uses NAMES for the help pages, so they match.
"""
import os, re, sys

NAMES = {
    # weapons, from language.lmp
    "FIREMACE": "NECROCANNON",
    "ETHEREAL CROSSBOW": "PLAGUEWIELDER",
    "DRAGON CLAW": "FROSTFANG",
    "HELLSTAFF": "BLOOD SCEPTRE",
    "PHOENIX ROD": "FIREBREATHER",
    "GAUNTLETS OF THE NECROMANCER": "VAMPYRIC CLAWS",
    # ammo
    "WAND CRYSTAL": "ACCURSED JEWEL",
    "CRYSTAL GEODE": "ACCURSED SEAL",
    "MACE SPHERES": "NECROSTEEL",
    "PILE OF MACE SPHERES": "GRIM NECROSTEEL",
    "ETHEREAL ARROWS": "PLAGUE BOLTS",
    "QUIVER OF ETHEREAL ARROWS": "QUIVER OF PLAGUE BOLTS",
    "CLAW ORB": "ICE SHARD",
    "ENERGY ORB": "ICE JEWEL",
    "LESSER RUNES": "BLOODSTONE",
    "GREATER RUNES": "ROYAL BLOODSTONE",
    "FLAME ORB": "FLAME TOOTH",
    "INFERNO ORB": "FLAME JAWS",
    # artifacts; the Morph Ovum and the Torch are "noname" there, so keep theirs
    "QUARTZ FLASK": "HEALING ELIXIR",
    "WINGS OF WRATH": "WINGS OF THE FALLEN",
    "RING OF INVINCIBILITY": "SHIELD OF THE IMMORTAL",
    "TOME OF POWER": "BLACK GRIMOIRE",
    "SHADOWSPHERE": "WRAITH CLOAK",
    "MYSTIC URN": "GRAIL OF LIFEBLOOD",
    "TIME BOMB OF THE ANCIENTS": "SIGIL OF DEATH",
    "CHAOS DEVICE": "MIRRORGATE",
    # armour and keys
    "SILVER SHIELD": "PLATE ARMOR",
    "ENCHANTED SHIELD": "WARLORD'S ARMOR",
    "YELLOW KEY": "GOLD KEY",
    "YOU NEED A YELLOW KEY TO OPEN THIS DOOR": "YOU NEED A GOLD KEY TO OPEN THIS DOOR",
    # skill levels
    "THOU NEEDETH A WET-NURSE": "WHIMPERING CRAVEN",
    "YELLOWBELLIES-R-US": "STILL A NOVICE",
    "BRINGEST THEM ONETH": "EXPERIENCED WARRIOR",
    "THOU ART A SMITE-MEISTER": "GRIM AND MORBID",
    "BLACK PLAGUE POSSESSES THEE": "DEATH'S RIGHT HAND",
}

# Maps, by their titles in CHANGELOG.md (0.1.4 > 0.1.5, where the 2017 maps
# came in; wadinfo.txt's comments for E1M7 predate it) and the commits that
# added E1M9 ("Courtyard of elements", 0c89a029) and reworked E3M2
# ("Shipwreck", 2ad7ee80), and E2M1's from language.lmp.  The rest of
# episode 3 has no names anywhere, and Heretic's are for other maps, so they
# go by their numbers.
MAPS = {
    "E1M1": "DEATH OF THE BLASPHEMER",   # Angry Saint
    "E1M2": "GRIM AWAKENING",            # Cacowad
    "E1M3": "TOWN OF AQUAFORT",          # SFoZ911
    "E1M4": "THE SEWERS",                # Steve Parker
    "E1M5": "FORGOTTEN STRONGHOLD",      # Snarboo
    "E1M6": "KHAZAD-DUM",                # Philippe Lesire
    "E1M7": "LUCIFER SPELL",             # Paul Corfiatis
    "E1M8": "BRAVADO",                   # Brad Kiefer
    "E1M9": "COURTYARD OF ELEMENTS",     # Fraggle
    "E2M1": "THE REMOTE OUTPOST",        # Owen "Sarge Baldy" Lloyd
    "E2M2": "TORTURE",                   # Chris Lutz
    "E2M3": "EVIL RUINS",                # Samian and Cacowad
    "E2M4": "THE WHITE CITADEL",         # Ryathaen
    "E2M5": "BREEZE",                    # Brad Kiefer
    "E2M6": "BRAVE",                     # Brad Kiefer
    "E2M7": "FIERY DOMUS",               # Cacowad
    "E2M8": "OBSIDIAN FORT",             # Cacowad
    "E2M9": None,                        # the placeholder map
    "E3M1": None,                        # Suporma
    "E3M2": "SHIPWRECK",                 # Craneo
    "E3M3": None,                        # Craneo
    "E3M4": None,                        # Ettingrinder, E3M4-7
    "E3M5": None,
    "E3M6": None,
    "E3M7": None,
    "E3M8": None,                        # Catoptromancy
    "E3M9": None,                        # the placeholder map
}


def heretic_strings(path):
    """Heretic's strings with their offsets in heretic.exe 1.0."""
    found = {}
    for off, s in re.findall(r'\{ \{\s*(\d+),\s*\d+,\s*\d+ \}, "((?:[^"\\]|\\.)*)" \}',
                             open(path).read()):
        found.setdefault(s, int(off))
    return found


def replacements(found):
    for e, title in MAPS.items():
        old = next(s for s in found if s.startswith(e + ":"))
        # the engine shows a map with nothing after its number by its number
        yield old, f"{e}:  {title}" if title else e
    yield from NAMES.items()


if __name__ == "__main__":
    found = heretic_strings(sys.argv[1])
    lines = ["Patch File for HHE v1.0", "",
             "# Blasphemer's own names: made by blasphemer/screens/names.py", ""]
    for old, new in replacements(found):
        if not found.get(old):
            sys.exit(f"no Heretic 1.0 offset for {old!r}")
        lines += [f"# {old}", f"Text {found[old]} {len(new)}", new, ""]
    with open(os.path.join(sys.argv[2], "hehacked.lmp"), "w", newline="\n") as f:
        f.write("\n".join(lines))
