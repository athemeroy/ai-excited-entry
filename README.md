# DON'T BLINK: Cosmic Eclipse Eye

[![make.fun · ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/athemeroy/ai-excited-entry/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/athemeroy/ai-excited-entry/reward.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

A 1024×1024 procedural space-art entry for make.fun: a giant cosmic eye with a total solar eclipse as its pupil, a retro rocket aimed at the eclipse, and `DON'T BLINK` pixel lettering.

## Procedural rendering layers

`draw.py` renders the artwork using only Python's standard library (`math`, `struct`, `zlib`), including rasterization, bitmap lettering, and PNG encoding.

- **Deep space nebula:** Layered noise creates violet and blue clouds, dark dust lanes, and a scattered star field.
- **Radial iris fibers:** Warped angular patterns form fine teal fibers and a jagged gold inner ring inside an almond-shaped eye.
- **Solar eclipse pupil:** A dark disk is edged with a bright corona, irregular streamers, red prominences, and a diamond-ring glint.
- **Retro rocket:** Rasterized polygons form the ship, with layered flame, glow, and sparks trailing behind it.
- **Pixel lettering:** A custom bitmap font draws the cream-colored `DON'T BLINK` title with a colored shadow.

## Local verification

From the repository root, run:

```bash
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
```

`main.ts` copies the checked-in `entry.png` to `out/entry.png`. It packages the existing artwork without rendering it again. To regenerate the source image separately, run `python3 draw.py`.
