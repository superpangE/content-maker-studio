---
name: blog
description: "Aggregation-based blog post pipeline. Input a category (e.g. 연예뉴스, 정치, 맛집) and the studio auto-collects Korean sources (Naver News + Naver Blog), picks an angle, rewrites into an original post, and produces platform-optimized final copy. Runs end-to-end without approval gates — just give it a category."
argument-hint: "<카테고리 또는 주제> — 예: 연예뉴스, 정치, 맛집, 또는 구체적 주제 (예: '뉴진스 최근 소식')"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Bash, Task, AskUserQuestion, Skill
model: sonnet
---

When this skill is invoked, you are the **orchestrator** of the aggregation
content pipeline. Your job is to run all stages automatically and deliver a
finished blog post — the user gives you a category, you deliver a ready-to-post
article.

## Philosophy

This is a **single-topic deep-dive studio**, not a roundup studio.
Every post focuses on **one specific story** sourced from real Korean content
(Naver News, Naver Blog). The pipeline picks the hottest single topic from the
category, then covers it thoroughly.

**Target depth: 1,500~2,500자 on ONE topic.** Do not bundle multiple unrelated
topics into one post. If sources yield 4 different stories, pick the best one
and go deep on it.

```
Category input
  → Source collection (Naver News + Naver Blog, 6-8 sources)
  → Topic selection (pick the single hottest story from sources)
  → Focused research on that one topic (re-search if needed)
  → Outline (deep structure for one topic)
  → Master draft (1,500~2,500자, one topic only)
  → Platform conversion (Naver / Tistory)
```

Run this pipeline without stopping for gates unless something goes wrong or
a decision requires the user's editorial judgment.

---

## 0. Setup & folder

1. Read `content/config/brand-voice.md`. If missing, proceed with defaults
   (friendly expert, 존댓말, no AI clichés).

2. Read the **format example** `content/config/blog-example.md` (structure +
   style reference). If it is missing, ask the user **once**:
   > 이 블로그의 형태(구조·문체) 참고할 example 글이 있나요? 붙여넣거나 파일 경로를 주세요. (없으면 건너뜁니다)
   - If they provide one, write it to `content/config/blog-example.md` and use it.
   - If they skip, write a sentinel file containing `(건너뜀 — example 없이 진행)`
     so this is never asked again; the user can add one later via `/setup-content`.
   - Treat a sentinel file the same as "no example".

3. Determine target platform: read `content/config/platforms/*.md`.
   - If both naver.md and tistory.md exist, produce both.
   - If only one exists, produce that one.

4. **Do not create the post folder yet** — wait until Step 1.5 when the
   single topic is selected. The slug will come from the topic name, not
   the category name.

   Resume logic (if a folder matching today's date + topic slug already exists):
   - If `draft.md` exists → skip to platform conversion.
   - If `outline.md` exists → skip to draft.
   - If `sources.md` exists → skip to outline.

---

## 1. Source Collection (broad) → raw sources

Spawn `source-collector` via Task. Pass:
- The category/topic argument
- Today's date
- Instruction: search broadly across the category, return 6-8 sources covering
  **different stories** within the category. Do not focus on one story yet.

After the agent completes, read the sources.

---

## 1.5. Topic Selection (YOU decide, no user gate)

Analyze the collected sources and **pick ONE topic** to write about. Choose
the topic that:
1. Has the most available source material (2+ sources covering the same story)
2. Is the most timely or interesting right now
3. Has enough depth to sustain 1,500~2,500자 on its own

**Derive the post slug from this selected topic** (not the category).
Create the post folder: `content/posts/<YYYY-MM-DD>-<topic-slug>/`

If the selected topic needs more source depth (only 1 source found), spawn
`source-collector` again with a narrower query targeting that specific topic.

Write `sources.md` into the post folder containing ONLY the sources relevant
to the selected topic.

---

## 2. Brief → brief.md

Spawn `content-strategist` via Task. Pass:
- `sources.md` content (focused on the single selected topic)
- `content/config/brand-voice.md` content
- The selected topic (not the category)

Ask it to:
1. Define the specific angle for this one topic
2. Identify what a reader would want to know deeply about this topic
3. Pick a primary keyword
4. Write brief.md

After the agent returns the brief, write `brief.md` immediately.

---

## 3. Outline → outline.md

Spawn `content-strategist` again via Task. Pass:
- `brief.md`
- `sources.md`
- `content/config/blog-example.md` content **if it is a real example** (skip if
  missing or a sentinel)

Ask it to produce an outline structured for **deep single-topic coverage**:
- 3-4 H2 sections, each going deeper into one aspect of the topic
- Each section: header + core message + which source feeds it + 자 budget
- Total target: 1,500~2,500자
- **If an example was passed**, use its section layout, length balance, and
  opening/closing pattern as the structural template (medium fidelity) — match
  the shape, fill it with this topic's content

Write `outline.md` immediately after it returns.

---

## 4. Master Draft → draft.md

Spawn `blog-writer` via Task. Pass:
- `content/config/brand-voice.md` content
- `brief.md` content
- `sources.md` content
- `outline.md` content
- `content/config/blog-example.md` content **if it is a real example** (skip if
  missing or a sentinel)

Instruct it to:
- Write from the sources, not from training memory
- Rewrite all facts in its own words
- Follow the outline structure
- **If an example was passed**, mirror its structure and writing style (rhythm,
  sentence feel, how sections open and close) — but never copy its sentences; the
  content comes from the outline and sources
- Return the full draft as text (do not write files)

After it returns, write `draft.md`.

---

## 5. Platform Conversion → naver.md / tistory.md

For each target platform, spawn `seo-editor` via Task. Pass:
- `draft.md` content
- `content/config/platforms/<platform>.md` content
- `brief.md` content

Instruct it to return the platform-optimized version as text only (no file
writes). After it returns, write `<platform>.md`.

---

## 6. Done

Print a summary:

```
✅ 완성: content/posts/<folder>/
  sources.md  — 수집된 소스
  brief.md    — 앵글 및 키워드
  outline.md  — 구조
  draft.md    — 마스터 초고
  naver.md    — 네이버 발행용
  tistory.md  — 티스토리 발행용 (해당 시)

발행: 각 플랫폼 파일을 복사해 직접 올려주세요.
```

---

## Error Handling

- **Source collection returns 0 results**: Tell the user, suggest a narrower
  or more specific search term, ask if they want to retry with a different term.
- **Agent fails mid-pipeline**: Tell the user which stage failed. The files
  written so far are intact — re-running `/blog <same topic>` will resume from
  the last completed stage.
- **Draft contains many `[확인 필요: ...]`**: List them at the end of the Done
  summary so the user knows to verify before publishing.
