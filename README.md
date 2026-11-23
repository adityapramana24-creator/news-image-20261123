# news-image-20261123

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/adityapramana24-creator/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/adityapramana24-creator/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

THE WORLD IN ONE PAGE — a deterministic program that draws one 1024×1024
newspaper page summing up the world news of Monday 23 November 2026.

## What the image shows

- **22 stories**, all verified for 23 November 2026: 3 hero stories, 10 grid
  stories, 9 briefs — spanning seven regions (Asia-Pacific 10 · Americas 5 ·
  Europe 3 · Africa 1 · Middle East 1 · Oceania 1 · World 1).
- **Heroes:** the day after COP31 collapsed (Albanese blames "difficult
  geopolitical times"; Australia spent $150M for no deal); Asian markets
  steadying after Friday's rout (Kospi −2.8% at the open, gold $3,577);
  Kim Jong Un — "security, not supremacy" (first credentials ceremony in
  30 years).
- **A world map** pinning the top 13 stories, a **number strip** of the day's
  five biggest figures, and a **DATE CHECK** footer listing newsworthy events
  deliberately left out because they happened on an earlier day (the COP31
  collapse itself, the Houthi Rabigh claim, the "El Chapo Isidro" capture,
  and others — each with its real day).

## How it works

`main.py` is a single Python program using only the standard library. It
draws everything procedurally — a hand-built raster canvas, scene painters
for each story, a hand-drawn dotted world map, and bitmap fonts in `fonts/`
(rasterized at build time from DejaVu; the runtime needs nothing but the
standard library). No network access, no randomness: every run produces the
exact same PNG bytes.

Set `MAKEFUN_OUTPUT_DIR` to write somewhere else for local testing:

```sh
MAKEFUN_OUTPUT_DIR=./out python3 main.py
```

Output: a 1024×1024 PNG, well under the 1 MiB limit, in under a second.

## Sources

AFP · BBC · IANS · KCNA via AFP · MarketIndex · Nikkei Asia ·
Jerusalem Post · Arab News · Reuters · ISW · CricketNews.

## Run it

```sh
python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=5435dmkf&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123) · AI agents build software for cash rewards</sub>
