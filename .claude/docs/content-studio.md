# Content Studio — Operating Guide

A lightweight studio for producing content (starting with blog posts) through a
small team of specialist agents and a gated, collaborative pipeline. Borrows the
game-studio philosophy: file-backed state, stage-by-stage approval, and
data-driven configuration.

## Agents

Shared across formats:

| Agent | Owns | Reads | Writes |
|---|---|---|---|
| **source-collector** | Retrieving raw Korean source material | category/topic (Naver News + Blog) | `sources.md` |
| **content-strategist** | Why / who / angle / keywords + structure | brand-voice, sources, topic | `brief.md`, `outline.md` |

Blog-specific:

| Agent | Owns | Reads | Writes |
|---|---|---|---|
| **blog-writer** | The platform-agnostic master draft (voice, flow) | brief, sources, outline, brand-voice | `draft.md` |
| **seo-editor** | Platform conversion & optimization | draft, platform profile, brief | `naver.md`, `tistory.md` |

Shorts-specific:

| Agent | Owns | Reads | Writes |
|---|---|---|---|
| **script-writer** | Vertical short-form script (hook/body/CTA, beats) | brief, sources, brand-voice | `script.md` |
| **shot-designer** | Per-shot production spec (Veo prompt + caption + TTS + timing) | script, shorts-style, platform profiles | `storyboard.md`, `shots.json` |

No separate director agent. The `/blog` and `/shorts` skills are the
orchestrators; the user gives a category and the pipeline runs to completion.

## Skills

- **`/setup-content`** — one-time (or anytime) setup of brand voice, platform
  profiles, and optional format examples. Run this first.
- **`/blog <카테고리>`** — single-topic blog pipeline. Source collection → topic
  selection → brief → outline → master draft → platform conversion.
- **`/shorts <카테고리>`** — single-topic short-form video pipeline. Source
  collection → topic selection → brief → script → storyboard + `shots.json` →
  `produce.sh`. Two-layer output: spec always (no keys), render when keys set.

## Pipeline

```
/blog <주제>
  0. Setup check (brand-voice, format example) + post folder
  1. Strategy   (content-strategist) → 🚦A → brief.md
  2. Research   (optional)           → 🚦B → research.md
  3. Outline    (content-strategist) → 🚦C → outline.md
  4. Draft      (blog-writer)        → 🚦D → draft.md
  5. Conversion (seo-editor)         → 🚦E → naver.md / tistory.md
```

Each artifact is written to file immediately on approval, so any interruption
resumes from the last saved stage.

## Shorts pipeline

```
/shorts <카테고리>
  0. Setup + read shorts-style.md + format example + platform profiles
  1. Source collection (source-collector, broad)      → sources (raw)
  1.5 Topic selection (orchestrator picks one story)   → sources.md + folder
  2. Brief        (content-strategist)                 → brief.md
  3. Script       (script-writer)                      → script.md
  4. Storyboard   (shot-designer)                      → storyboard.md + shots.json
  5. Render layer (orchestrator copies template)       → produce.sh
```

**Two layers.** Layer 1 (spec) always runs and needs no API keys —
`script.md` / `storyboard.md` / `shots.json` fully describe the video. Layer 2
(`produce.sh`) renders the actual 9:16 MP4 by calling a TTS API (ElevenLabs) and
a text-to-video API (Veo), then assembling with ffmpeg. With no keys set,
`produce.sh` prints what's needed and exits cleanly.

## Directory conventions

```text
content/
├── config/
│   ├── brand-voice.md          # persona, tone, forbidden expressions
│   ├── blog-example.md         # blog form reference (structure + style)
│   ├── shorts-example.md       # shorts form reference (structure + style)
│   ├── shorts-style.md         # locked motion-graphics visual identity (Veo base)
│   └── platforms/
│       ├── naver.md            # Naver blog conversion rules
│       ├── tistory.md          # Tistory/WordPress (Google SEO) rules
│       ├── shorts-youtube.md   # YouTube Shorts (≤60s) profile
│       ├── shorts-reels.md     # Instagram Reels (≤90s) profile
│       └── shorts-tiktok.md    # TikTok profile
├── posts/
│   └── YYYY-MM-DD-<slug>/       # one blog post = one folder
│       ├── sources.md · brief.md · outline.md · draft.md
│       ├── naver.md · tistory.md
└── shorts/
    └── posts/
        └── YYYY-MM-DD-<slug>/   # one short = one folder
            ├── sources.md · brief.md · script.md
            ├── storyboard.md · shots.json · produce.sh
```

## Design principles

- **File = memory.** Every approved stage is on disk; conversation is secondary.
- **One post = one folder.** All artifacts for a post live together.
- **Master draft, then convert.** Write `draft.md` once (platform-agnostic), then
  produce per-platform versions. Never re-write the body per platform.
- **Example = form.** `*-example.md` teaches structure and style (the shape);
  topic and facts always come fresh from sources. Captured once, reused every run.
- **Data-driven platforms.** Platform rules live in config files; conversion
  logic lives in the seo-editor. Adding a platform = adding one profile file.

## Extending to new content types

To add shorts (or any new format), follow the same pattern:
1. Add config if needed (e.g., `content/config/platforms/youtube-shorts.md`).
2. Add a specialist agent for the new craft (e.g., `script-writer`).
3. Add an orchestrator skill (e.g., `/shorts`) with the same gated pipeline.
4. Reuse `content-strategist` — topic/angle decisions are shared across formats.

## Relationship to the game-studio template

This project was scaffolded from a game-studio template. The game agents
(`.claude/agents/*` for game roles), game skills (`brainstorm`, `design-system`,
etc.), templates, and the `design/` `src/` `production/` trees still exist but
are **not part of the content workflow**. They are left in place for reference
and are not deleted.
