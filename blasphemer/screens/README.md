# Screens

The help pages, credits and episode endings, made from Blasphemer's own
graphics: its fonts, artifact icons, status bar and flats, and views rendered
from its levels by the engine. They replace placeholders that all showed one
page (`lumps/readme.png`). The menu's graphics are made here too (below).

| Lump   | File                | Shows                                          |
| ------ | ------------------- | ---------------------------------------------- |
| HELP1  | `lumps/helpbar.png`  | the status bar and the artifacts (F1)          |
| HELP2  | `lumps/helpkeys.png` | the default controls (F1, next page)           |
| CREDIT | `lumps/credits.png`  | everyone in `CREDITS.md`, and the engine       |
| E2END  | `lumps/e2vista.png`  | after episode 2: E2M3's river valley           |
| FINAL1 | `lumps/e3window.png` | after episode 3: E3M3's pentagram window ...   |
| FINAL2 | `lumps/e3stars.png`  | ... then the scroll up into the stars, the end |
| E2PAL  | `lumps/e2pal.lmp`    | E2END's palette: the game's own                |

To make them again, say after changing the default keys, from the top of the
repo with `blasphem.wad` built and the engine built:

```sh
python3 blasphemer/screens/render.py build/src/crispy-heretic blasphemer/blasphem.wad blasphemer/screens/shots
python3 blasphemer/screens/make_screens.py blasphemer/blasphem.wad blasphemer/screens/shots blasphemer/lumps
make -C blasphemer blasphem.wad
```

`render.py` runs the game off-screen under gdb and needs gdb and Pillow; it
writes the views to `shots/`, which are kept, so changing the text only needs
`make_screens.py`. Camera spots are in `render.py`, the text in
`make_screens.py`. Everything stays in the WAD's palette.

## Menu graphics

`make_menu.py` makes the menu graphics Blasphemer had left as placeholders,
into `graphics/`:

| Lump              | Shows                                                    |
| ----------------- | -------------------------------------------------------- |
| M_SKL00-17        | the skull medallion (PSKULL) spinning beside the title   |
| M_FSLOT           | a save slot: the status bar's stone in a silver frame    |
| M_SLDLT, M_SLDRT  | the slider's ends, silver with a red jewel               |
| M_SLDMD1, M_SLDMD2| the slider's rail, in turn; the first has a tick below   |

```sh
python3 blasphemer/screens/make_menu.py blasphemer/blasphem.wad blasphemer/graphics
rm blasphemer/blasphem.wad blasphemer/blasphdm.wad; make -C blasphemer blasphem.wad
```

It reads only the WAD, not the engine. The offsets are in `wadinfo.txt` and
`BlasphDM.txt`, and the script's comments say why they are what they are.

## Intermission maps

`make_maps.py` makes the maps shown between the levels of episodes 1 to 3,
and the marks the engine puts on them, into `graphics/`:

| Lump     | Shows                                                          |
| -------- | -------------------------------------------------------------- |
| MAPE1    | episode 1: an island, with forests, hills and rivers           |
| MAPE2    | episode 2: scorched land in a sea of lava, with volcanoes      |
| MAPE3    | episode 3: a coast on a grey sea                               |
| IN_X     | a red cross on each level that's done                          |
| IN_YAH   | a gold arrow over the next level, blinking                     |

Each level's place stands where `src/heretic/in_lude.c` (`YAHspot`) puts its
marks, and roads join each place to its nearest neighbours; the land around
them is made up from seeded noise, so it comes out the same every time. The
seeds, colours and what stands at each place are at the top of the script.

```sh
python3 blasphemer/screens/make_maps.py blasphemer/blasphem.wad blasphemer/graphics
```

It needs numpy and Pillow.
