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

### Changed

- True-colour rendering is built in by default, so light fades smoothly with distance
  instead of in bands.
- Uncapped framerate is on by default, so the picture moves smoothly on a 60 Hz or faster
  screen instead of at 35 frames a second.
- The automap's background is drawn at the same scale at every resolution, as in the
  original game.
- With permanent mouselook on, landing from a fall or a jump no longer pulls the view back to
  the centre.
