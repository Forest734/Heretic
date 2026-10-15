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
  1-3 are mostly complete, and art is still missing or rough in places: `wadinfo.txt` still
  marks LOADING (unused by the engine) and DEMO1-2 as placeholders, though both demos play in
  step. DEMO3 didn't, so it's left out, and the title loop skips a demo the WAD hasn't got.

What the fork changes so far is in CHANGELOG.md. Every change to upstream code is marked
`// [heretic]`, as Crispy marks its own `// [crispy]`, so `git grep '\[heretic\]'` finds them.

## Commands

```sh
cmake -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo   # once
cmake --build build --target crispy-heretic -j"$(nproc)"   # ~15 s from clean
make -C blasphemer blasphem.wad                    # the game data: blasphem.wad and blasphdm.wad
make -C blasphemer install prefix=$HOME/.local     # to ~/.local/share/games/doom, where it's found
./build/src/crispy-heretic                         # finds blasphem.wad by itself once installed
./build/src/crispy-heretic -iwad blasphemer/blasphem.wad -warp 1 1 -skill 3   # straight into E1M1
```

The Makefile doesn't know what the WADs are made from, so after changing anything in
`blasphemer/`, delete `blasphem.wad` and `blasphdm.wad` before making them again.

`CRISPY_TRUECOLOR` is on by default here (upstream: off). The autotools build
(`configure.ac`) wasn't changed and still defaults to 8-bit, so use CMake.

**Dependencies.** With root: `sudo apt install cmake pkg-config libsdl2-dev
libsdl2-mixer-dev libsdl2-net-dev libpng-dev libsamplerate0-dev deutex`. Until the user runs
that, the build uses a no-root copy: `cmake` from `pipx install cmake`, and SDL2, SDL2_mixer,
SDL2_net and their runtime libraries `apt-get download`ed and `dpkg -x`ed into
`~/.local/opt/heretic-deps/root` (the `.deb`s are in `../debs`; dangling `libpng16`/
`libsamplerate` symlinks there point at the system's copies). Configure against it with:

```sh
R=~/.local/opt/heretic-deps/root/usr; L=$R/lib/x86_64-linux-gnu
cmake -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_PREFIX_PATH=$R \
  -DSDL2_INCLUDE_DIR=$R/include/SDL2 -DSDL2_LIBRARY=$L/libSDL2-2.0.so \
  -DSDL2_MIXER_INCLUDE_DIR=$R/include/SDL2 -DSDL2_MIXER_LIBRARY=$L/libSDL2_mixer-2.0.so \
  -DSDL2_NET_INCLUDE_DIR=$R/include/SDL2 -DSDL2_NET_LIBRARY=$L/libSDL2_net-2.0.so \
  -DSAMPLERATE_INCLUDE_DIR=$R/include -DSAMPLERATE_LIBRARY=$L/libsamplerate.so \
  "-DCMAKE_C_FLAGS=-isystem $R/include/x86_64-linux-gnu" \
  "-DCMAKE_EXE_LINKER_FLAGS=-Wl,--disable-new-dtags -Wl,-rpath,$L/sdl2-classic:$L"
```

The RPATH (not RUNPATH) lets the binaries run without `LD_LIBRARY_PATH`. Once the system
packages are installed, delete `build/` and configure plainly.

The WADs need `deutex`; without root, `apt-get download deutex` and `dpkg -x` it (the binary
is in `usr/games/`). The Makefile's `python` step only regenerates `lumps/sndcurve.lmp`, which
is committed, so it's skipped unless `blasphemer_sndcurve.py` changes (then use `python3`).

## Testing

There are no unit tests; upstream's `quickcheck/` plays vanilla demos, which need Raven's
WADs. Check changes by running the game off-screen under gdb (ptrace only works on a child, so
launch it from gdb rather than attaching):

```sh
SDL_VIDEODRIVER=offscreen SDL_AUDIODRIVER=dummy SDL_RENDER_DRIVER=software gdb -q -batch \
  -ex 'break P_Ticker if leveltime == 70' -ex run -ex 'call V_ScreenShot("SHOT%02i.%s")' -ex kill \
  --args build/src/crispy-heretic -iwad blasphemer/blasphem.wad -warp 1 1 -skill 3 -nomusic \
  -window -geometry 1280x720 -config /tmp/x/heretic.cfg -extraconfig /tmp/x/crispy-heretic.cfg \
  -savedir /tmp/x/saves
```

- Run it from a scratch directory: screenshots are PNGs in the current directory, read back
  from the renderer, so they show exactly what a player sees. `-config`/`-extraconfig`/
  `-savedir` keep the user's settings out of it. Without `SDL_RENDER_DRIVER=software` and a
  window size, the offscreen frame lands in a corner of a bigger image.
- Drive the game from gdb: `set var crispy->jump = 2`, `set var gamekeydown[key_jump] = 1`,
  then a `break P_Ticker if leveltime >= N` with `commands` printing `players[0].mo->z` etc.
  The menu pauses the game, so break on `I_FinishUpdate` instead. To open a menu, set
  `CurrentMenu = &Crispness3Menu`, `crispnessmenupage = 2` after `call MN_ActivateMenu()`
  (`SetMenu` is inlined away). `call I_Quit()` exits cleanly and saves the config.
- Don't point `DOOMWADDIR` at `blasphemer/`: its `heretic.wad` is a 10 KB deutex stub, and
  `heretic.wad` wins the IWAD search.
- `-record` turns off everything in `critical`, so recording is how to check a gameplay
  option stays out of demos.

## Game data

`blasphemer/` is source for deutex: `wadinfo.txt` lists every lump and where it comes from
(`levels/`, `graphics/`, `sprites/`, `flats/`, `patches/`, `textures/`, `sounds/`,
`musics/`, `lumps/`). The built `blasphem.wad` (single player) and `blasphdm.wad`
(deathmatch) are ignored. Never commit Raven's `heretic.wad` or `heretic1.wad`.

The help pages, credits and endings (HELP1/2, CREDIT, E2END, E2PAL, FINAL1/2) are ours, made
by `blasphemer/screens/` from Blasphemer's own fonts, icons and level views; its README says
how to make them again (after changing default keys, say). Both `wadinfo.txt` and
`BlasphDM.txt` list them.

Blasphemer marks itself with an empty `BLASPHEM` lump and has the `EXTENDED` lump, so it runs
as the five-episode retail game. `src/d_iwad.c` knows `blasphem.wad` by name, ranked between
`heretic.wad` and `heretic1.wad`; `src/heretic/d_main.c` titles it "Blasphemer" and keeps its
saves in `savegames/blasphem.wad/`, apart from Heretic's. Settings go in
`~/.local/share/crispy-doom/`.

## Layout

- `src/heretic/` is the game: `p_*` play (`p_enemy.c` monsters, `p_inter.c` pickups and
  damage, `p_pspr.c` weapons, `p_user.c` the player, `p_mobj.c` movement and landing), `r_*`
  the renderer, `sb_bar.c` the status bar, `am_map.c` the automap, `mn_menu.c` the menus (the
  Crispness pages hold Crispy's options), `info.c` the thing and state tables, `deh_*`
  DeHackEd patches.
- `src/` holds what the four games share: `i_*` the SDL platform layer (`i_video.c`),
  `v_video.c` drawing and screenshots, `m_config.c` settings, `m_controls.c` key bindings,
  `d_iwad.c` the IWAD search. A change here reaches Doom, Hexen and Strife as well, so build
  all targets after one. `crispy->hires` is a shift (320x200 << hires); Heretic goes to 2
  (4x), and `max_hires` in `i_video.c` holds the other games to 1, as upstream.
- `src/crispy.h` is the `crispy` struct of options, shared by all four games. A Heretic
  option needs binding in `src/heretic/d_main.c` (`D_BindVariables`) and, for the setup tool,
  in the Heretic block of `src/setup/compatibility.c`; the setup tool shows controls per game
  in `src/setup/keyboard.c`, `mouse.c` and `joystick.c`.

## Upstreams

`origin` is `git@github-forest734:Forest734/Heretic.git`, and the branch is `main`.

- `upstream` is fabiangreffrath/crispy-doom. Bring in its releases with
  `git fetch upstream && git merge crispy-doom-<version>`. Small, local changes merge more
  easily than rewrites of upstream files.
- `blasphemer` is Blasphemer/blasphemer, merged in as a subtree at `blasphemer/` (its history
  is kept). It hasn't been active since 2023; if it moves, pull with
  `git fetch blasphemer && git merge -X subtree=blasphemer/ blasphemer/master`.
- Upstream's GitHub workflows run on pushes to `master`, so none run on this fork's `main`.

## Conventions

- Gameplay changes go behind an option, defaulting to off, so the original game stays
  playable. Read them through `critical->` rather than `crispy->`: `critical` is all zeros
  while recording or playing a demo and in netgames (`CheckCrispySingleplayer`), which keeps
  demos in sync, since demos record inputs only. Heretic's `player->lookdir` aims shots, so
  even view changes can be gameplay here.
- Spare bits in `ticcmd_t` carry new inputs, as `AFLAG_JUMP` (0x80) does in `arti`, where
  artifact numbers stay below it and 0xff means "next artifact". `player_t` fields aren't
  saved unless `p_saveg.c` writes them; new ones that only matter for a few tics needn't be.
- Blasphemer's art uses its own palette (`blasphemer/blasphemer-palette_v2.gpl`); new
  graphics have to be drawn in it.
- CHANGELOG.md follows Keep a Changelog; add user-facing changes under [Unreleased].
- Upstream's C style: 4-space indents, braces on their own line, C99.
