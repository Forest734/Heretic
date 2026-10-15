# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

heretic is a free Heretic, improved in graphics and gameplay. It has two parts:

- **The engine** is a fork of Crispy Doom 7.2 (`fdeabe4c`), which builds on Chocolate Doom
  and Raven's 1999 source release. Only `crispy-heretic` is ours to change. The other games'
  code stays in the tree because all four share `src/`, and keeping it makes upstream merges
  simple. It's GPL-2.0-or-later (`COPYING.md`), and the fork has to stay under it.
- **The game data** is Blasphemer 0.1.8+ (`5d858ad`, March 2023) in `blasphemer/`: free
  levels, graphics, sound and music made to replace Heretic's, so nothing needs buying. It's
  BSD-3-Clause (`blasphemer/COPYING.md`); `blasphemer/CREDITS.md` names its authors. Episodes
  1-3 are mostly complete, and art is still missing or rough in places.

## Commands

```sh
cmake -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo   # once
cmake --build build --target crispy-heretic -j"$(nproc)"
make -C blasphemer blasphem.wad                    # the game data: blasphem.wad and blasphdm.wad
./build/src/crispy-heretic -iwad blasphemer/blasphem.wad
./build/src/crispy-heretic -iwad blasphemer/blasphem.wad -warp 1 1 -skill 3   # straight into E1M1
```

The engine needs `cmake pkg-config libsdl2-dev libsdl2-mixer-dev libsdl2-net-dev libpng-dev
libsamplerate0-dev` (`libfluidsynth-dev` is optional). The WADs need `deutex`; without root,
`apt-get download deutex` and `dpkg -x` it, as `~/CLAUDE.md` does for potrace (the binary is
in `usr/games/`). The Makefile's `python` step only regenerates `lumps/sndcurve.lmp`, which is
committed, so it's skipped unless `blasphemer_sndcurve.py` changes (then run it with
`python3`). `quickcheck/` holds upstream's demo playback check.

## Game data

`blasphemer/` is source for deutex: `wadinfo.txt` lists every lump and where it comes from
(`levels/`, `graphics/`, `sprites/`, `flats/`, `patches/`, `textures/`, `sounds/`,
`musics/`, `lumps/`). The built `blasphem.wad` (single player) and `blasphdm.wad`
(deathmatch) are ignored. `blasphemer/heretic.wad` is a 10 KB stub deutex reads, not
Heretic's data. Never commit Raven's `heretic.wad` or `heretic1.wad`.

Crispy only recognises `heretic.wad` and `heretic1.wad` by name (the table at the top of
`src/d_iwad.c`), so Blasphemer needs `-iwad` for now. Settings and saves go in
`~/.local/share/crispy-doom/`.

## Layout

- `src/heretic/` is the game: `p_*` play (`p_enemy.c` monsters, `p_inter.c` pickups and
  damage, `p_pspr.c` weapons, `p_user.c` the player), `r_*` the renderer, `sb_bar.c` the status
  bar, `am_map.c` the automap, `mn_menu.c` the menus (the Crispness pages hold Crispy's options),
  `info.c` the thing and state tables, `deh_*` DeHackEd patches.
- `src/` holds what the four games share: `i_*` the SDL platform layer (`i_video.c`),
  `v_video.c` drawing, `m_config.c` settings, `d_iwad.c` the IWAD search. A change here reaches
  Doom, Hexen and Strife as well, so it has to build for them too.
- `src/crispy.h` is the `crispy` struct of options; settings are bound in `m_config.c`.

## Upstreams

`origin` is `git@github-forest734:Forest734/Heretic.git`, and the branch is `main`.

- `upstream` is fabiangreffrath/crispy-doom. Bring in its releases with
  `git fetch upstream && git merge crispy-doom-<version>`. Small, local changes merge more
  easily than rewrites of upstream files.
- `blasphemer` is Blasphemer/blasphemer, merged in as a subtree at `blasphemer/` (its history
  is kept). It hasn't been active since 2023; if it moves, pull with
  `git fetch blasphemer && git merge -X subtree=blasphemer/ blasphemer/master`.

## Conventions

- Gameplay changes go behind an option, defaulting to off, so the original game stays
  playable. Demos record inputs only, so any gameplay change desyncs them: in demo playback
  and recording, and in netgames, keep the original behaviour.
- Blasphemer's art uses its own palette (`blasphemer/blasphemer-palette_v2.gpl`); new
  graphics have to be drawn in it.
- Upstream's C style: 4-space indents, braces on their own line, C99.
