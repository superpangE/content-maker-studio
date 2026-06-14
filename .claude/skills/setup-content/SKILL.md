---
name: setup-content
description: "Configure the content studio's brand voice and platform profiles. Run once before /blog (or anytime to update). Creates content/config/brand-voice.md and per-platform profiles that all content generation respects."
argument-hint: "no args for guided setup | refresh to review existing config"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, AskUserQuestion
model: sonnet
---

When this skill is invoked:

## 1. Check existing config

Read these if they exist:
- `content/config/brand-voice.md`
- `content/config/platforms/naver.md`
- `content/config/platforms/tistory.md`

If they already exist, tell the user they're configured and show a one-line
summary of each (persona/tone, and which platforms have profiles). Ask whether
they want to **update** them or **leave as-is**. If `refresh` was passed, go
straight to reviewing existing values section by section.

If they don't exist, note that defaults will be created and proceed.

## 2. Brand voice (guided)

Walk through these one topic at a time using `AskUserQuestion` where the choice
is constrained, plain text where it's open. Do NOT ask everything at once.

- **페르소나**: 어떤 화자인가? (친근한 전문가 / 솔직한 후기러 / 담백한 정보 전달자 / 직접 설명)
- **톤**: 어조와 분위기 (존댓말 차분 / 활기참 / 담백 정보 위주 / 직접 설명)
- **독자 호칭**: 자유 입력 (여러분 / 구독자님 / …)
- **1인칭 경험 포함 여부**: 허용 / 비허용
- **금지어·피할 표현**: 자유 입력 (과장 광고, AI 상투어 등)
- **시그니처 표현**(선택): 자유 입력

For each answer, confirm, then write to `content/config/brand-voice.md`. Mirror
the structure of the default file already in the repo. Ask
"May I write this to content/config/brand-voice.md?" before writing.

## 3. Platform profiles

Ask which platforms the user publishes to (`AskUserQuestion`, multiSelect):
네이버 블로그 / 티스토리 / 워드프레스 / 기타.

For each selected platform, confirm or adjust the profile fields: 제목 규칙,
본문 구조, 톤, SEO 규칙, 분량, 금지 사항. Sensible defaults already exist for
네이버 (`platforms/naver.md`) and 티스토리/워드프레스 (`platforms/tistory.md`) —
present those defaults and let the user tweak rather than starting from blank.

For a new platform not yet profiled, create `content/config/platforms/<slug>.md`
following the same structure as the existing profiles. Ask before writing each
file.

## 4. Confirm and hand off

Summarize what was written. Tell the user they can now run:

> `/blog [주제]` — to generate a blog post end to end.

Remind them they can edit the config files directly anytime; the studio reads
them fresh on every `/blog` run.
