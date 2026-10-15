# Changelog

All notable changes to heretic are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Changes that come from Crispy Doom
itself are in NEWS.md.

## [Unreleased]

### Added

- Blasphemer, the free replacement for Heretic's game data, is included and found by itself:
  `blasphem.wad` in any IWAD directory starts the game with no `-iwad` needed. The window and
  startup banner say "Blasphemer", and its saves are kept apart from Heretic's.
- Jumping, as in Hexen: Options → Crispness → page 3 → Jumping (off, low, high; off by default).
  Low jumps 36 units and high 45, as in Crispy Doom; a chicken hops lower. The jump key defaults
  to `/` and can be set in the setup tool (keyboard, mouse or controller). Jumping is off while
  recording or playing demos and in netgames, so demos stay compatible with Heretic.
- Rendering at 4x (1280 x 800, wider in widescreen), now the default: Options → Crispness →
  page 1 → High resolution rendering (off, 2x, 4x). Edges and distant walls are much sharper
  on a 1080p or larger screen.
- Real help, credits and ending screens in place of Blasphemer's placeholder, which showed
  the same "Blasphemer is Free and Open-Source Software" page for all of them: F1 explains
  the status bar and the artifacts, then the controls; the credits name everyone in
  Blasphemer's CREDITS.md; episode 2 ends on a view of E2M3's river valley, and episode 3 on
  E3M3's pentagram window before scrolling up into the stars. They're built from
  Blasphemer's own graphics and levels by `blasphemer/screens/`.
- Brightmaps made for Blasphemer's own art, and on by default: lava and lavafalls, runes,
  stained glass, teleporter pentagrams, the gems and crosses on exit doors and some demons'
  eyes glow in the dark, as do the Torch's flame, the Phoenix Rod's orbs and a Disciple's
  mouth as it attacks. Crispy's brightmaps were drawn for Heretic's textures and lit the wrong parts of
  Blasphemer's, or nothing. Options → Crispness → page 1 → Apply brightmaps to (none, walls,
  items, both).
- Menu graphics where Blasphemer had placeholders: a skull medallion spins on each side of
  the title, the save and load slots can be seen (before, the menu showed nothing where
  they were), and the volume, screen size and mouse sliders have a rail to move along
  instead of a lone gem. They're built from Blasphemer's own art by `blasphemer/screens/`.
- Maps between levels: after each level of episodes 1 to 3, the episode's map is shown, as in
  Heretic, with a red cross on every level done and a gold arrow on the next. Blasphemer had
  only a blank screen there. They're drawn as ink on parchment, one land for each episode
  (an island; scorched land in a lava sea; a grey coast), by `blasphemer/screens/`.

### Fixed

- The end of episode 2 was drawn in the wrong colours: its palette (E2PAL) was a placeholder
  too. It's now the game's own.

### Changed

- True-colour rendering is built in by default, so light fades smoothly with distance
  instead of in bands.
- Uncapped framerate is on by default, so the picture moves smoothly on a 60 Hz or faster
  screen instead of at 35 frames a second.
- The automap's background is drawn at the same scale at every resolution, as in the
  original game.
- With permanent mouselook on, landing from a fall or a jump no longer pulls the view back to
  the centre.
- The title and credit pages are darkened behind the menu and the quit question, so they
  can be read over Blasphemer's title, which has its name in red right where the menu goes.
