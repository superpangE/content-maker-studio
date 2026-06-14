---
name: shorts
description: "Aggregation-based short-form video pipeline. Input a category (e.g. 국내야구, 연예뉴스, 정치) and the studio auto-collects Korean sources (Naver News + Naver Blog), picks one hot topic, writes a vertical (9:16) script, and produces a full production spec — per-shot Veo prompts, captions, TTS lines, and a runnable produce.sh that renders the actual video once API keys are set. Targets YouTube Shorts / Reels / TikTok."
argument-hint: "<카테고리 또는 주제> — 예: 국내야구, 연예뉴스, 정치, 또는 구체적 주제"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Bash, Task, AskUserQuestion, Skill
model: sonnet
---

When this skill is invoked, you are the **orchestrator** of the short-form video
pipeline. The user gives you a category; you deliver a finished **production
spec** for one vertical short — ready to render.

## Philosophy

This is a **single-topic short-form studio**. Every short focuses on **one
specific story** sourced from real Korean content (Naver News, Naver Blog). The
pipeline picks the hottest single topic from the category, writes a tight
9:16 script, and turns it into a shot-by-shot production spec.

**One topic per short. 40~60초. 8~12 shots.** Do not bundle multiple stories.

### Two-layer output (important)

This studio builds in **two layers** because video/voice generation needs paid
external API keys that may not be set yet:

- **Layer 1 — Spec (always works, no keys):** `script.md`, `storyboard.md`,
  `shots.json`. The complete plan. This is what `/shorts` always produces.
- **Layer 2 — Render (works when keys are set):** `produce.sh` reads
  `shots.json`, calls the TTS API (ElevenLabs) and video API (Veo), and
  assembles a 9:16 MP4 with ffmpeg. If keys are missing it prints what's needed
  and exits cleanly — it does NOT fail the pipeline.

```
Category input
  → Source collection (Naver News + Naver Blog)        [source-collector]
  → Topic selection (pick the single hottest story)    [orchestrator]
  → Brief (angle, keyword, audience)                   [content-strategist]
  → Script (hook → body → CTA, beat by beat)           [script-writer]
  → Storyboard + shots.json (per-shot Veo/TTS/caption)  [shot-designer]
  → produce.sh (copy render template into the folder)  [orchestrator]
```

Run the pipeline without stopping for gates unless something goes wrong or a
decision needs the user's editorial judgment.

---

## 0. Setup & folder

1. Read `content/config/brand-voice.md`. If missing, proceed with defaults
   (friendly expert, 존댓말, no AI clichés).

2. Read `content/config/shorts-style.md` (the locked visual identity). If
   missing, proceed with motion-graphics defaults but note it.

3. Determine target platforms: check `content/config/platforms/shorts-*.md`.
   - Produce a spec for every `shorts-<platform>.md` that exists
     (youtube / reels / tiktok). The single set of shots is shared; only CTA
     captions and total length differ per platform (shot-designer handles this).

4. **Do not create the post folder yet** — wait until Step 1.5 when the single
   topic is selected. The slug comes from the topic name, not the category.

   Resume logic (if a folder matching today's date + topic slug already exists
   under `content/shorts/posts/`):
   - If `shots.json` exists → skip to Step 6 (produce.sh + done).
   - If `script.md` exists → skip to Step 5 (storyboard).
   - If `brief.md` exists → skip to Step 4 (script).
   - If `sources.md` exists → skip to Step 3 (brief).

---

## 1. Source Collection (broad) → raw sources

Spawn `source-collector` via Task (Mode A — broad scan). Pass:
- The category/topic argument
- Today's date
- Instruction: search broadly across the category, return 6-8 sources covering
  **different stories**. Do not focus on one story yet.

After the agent completes, read the sources.

---

## 1.5. Topic Selection (YOU decide, no user gate)

Analyze the collected sources and **pick ONE topic**. Choose the topic that:
1. Has the most source material (2+ sources on the same story)
2. Is the most timely/interesting right now
3. Has a clear hook that works in a 3-second opening

**Derive the slug from the selected topic** (not the category).
Create the post folder: `content/shorts/posts/<YYYY-MM-DD>-<topic-slug>/`

If the topic needs more depth (only 1 source), spawn `source-collector` again
(Mode B — focused) with a narrow query targeting that topic.

Write `sources.md` into the folder containing ONLY the sources relevant to the
selected topic.

---

## 2. Brief → brief.md

Spawn `content-strategist` via Task (shared with the blog pipeline). Pass:
- `sources.md` content (focused on the single topic)
- `content/config/brand-voice.md` content
- The selected topic
- Note: this is for a **short-form video**, so the angle should be punchy and
  hook-driven, and the "심층 커버 포인트" should be 3-4 beats that fit a 60초 short.

Write `brief.md` immediately after it returns.

---

## 3. Script → script.md

Spawn `script-writer` via Task. Pass:
- `content/config/brand-voice.md` content
- `brief.md` content
- `sources.md` content

Instruct it to:
- Write from the sources, not from training memory
- Structure as hook (0~3초) → body → CTA, 8~12 beats, 40~60초
- Return the full beat-numbered script as text (no file writes)

After it returns, write `script.md`.

---

## 4. Storyboard + shots.json → storyboard.md / shots.json

Spawn `shot-designer` via Task. Pass:
- `script.md` content
- `content/config/shorts-style.md` content
- The list of target platform profiles (`content/config/platforms/shorts-*.md`
  contents) so it can set per-platform CTA variants and check total length
- `brief.md` content (for the primary keyword)

Instruct it to return BOTH `storyboard.md` and `shots.json` as text (no file
writes). After it returns:
- Write `storyboard.md`.
- Validate `shots.json` is valid JSON before writing (run `python3 -c "import
  json,sys; json.load(open('<path>'))"` after writing, or parse the text first).
  If invalid, ask the shot-designer to fix it. Then write `shots.json`.

---

## 5. produce.sh (Layer 2 render script)

Copy the render template into the post folder so the short can be rendered once
keys are set:

```bash
cp .claude/skills/shorts/produce.sh "content/shorts/posts/<folder>/produce.sh"
chmod +x "content/shorts/posts/<folder>/produce.sh"
```

`produce.sh` reads `shots.json` in its own folder. It does NOT need keys to be
copied — it checks for them at run time and explains what's missing.

---

## 6. Done

Print a summary:

```
✅ 완성 (스펙): content/shorts/posts/<folder>/
  sources.md    — 수집된 소스
  brief.md      — 앵글 및 키워드
  script.md     — 쇼츠 대본 (훅/본문/CTA)
  storyboard.md — 장면별 비주얼·자막·내레이션 (사람이 읽는 명세)
  shots.json    — 기계가 읽는 명세 (Veo 프롬프트 + TTS + 자막 + 타이밍)
  produce.sh    — 실제 영상 렌더 스크립트

🎬 실제 영상 렌더 (선택):
  API 키를 설정한 뒤 폴더에서 ./produce.sh 실행:
    export ELEVENLABS_API_KEY=...   # TTS
    export VEO_API_KEY=...          # 영상 생성
  키가 없으면 produce.sh가 무엇이 필요한지 안내하고 종료합니다.

타겟: YouTube Shorts / Reels / TikTok (shots.json의 cta_variants 참고)
```

If the script contains `[확인 필요: ...]` markers, list them here so the user
verifies before rendering.

---

## Error Handling

- **Source collection returns 0 results**: Tell the user, suggest a narrower
  search term, ask whether to retry.
- **shots.json fails JSON validation**: re-spawn shot-designer to fix; do not
  write invalid JSON.
- **Agent fails mid-pipeline**: tell the user which stage failed. Files written
  so far are intact — re-running `/shorts <same topic>` resumes from the last
  completed stage (see Step 0 resume logic).
