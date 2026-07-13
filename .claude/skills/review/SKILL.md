---
name: review
description: "Photo-driven Korean review-post pipeline for Naver Blog. Give it a photo folder and a rough description; it reads the photos, interviews you for what's missing, fills factual gaps with web search, writes the post in your own template's shape, and publishes it to your Naver blog headlessly. Handles 맛집·여행·제품·장소 reviews."
argument-hint: "<사진 폴더 경로> <대충 설명> — 예: ./photos/ 어제 성수동 파스타집 갔는데 트러플 파스타 맛있었음"
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, Task, AskUserQuestion, WebSearch, WebFetch
model: sonnet
---

When this skill is invoked you are the **orchestrator** of the review-post
pipeline. The user hands you photos and a rough, incomplete description of an
experience. You deliver a published Naver blog post.

The user's photos and memory are the **primary source**. Web search is only
there to fill factual gaps (address, hours, price). Never write the post from
training memory, and never invent a fact to make a sentence flow.

```
photos + rough description
  → Read the photos      (extract every fact visible in them)
  → Scout                (what is this place KNOWN for? — before asking anything)
  → Interview            (lead with the signature experience, then fill gaps)
  → Research             (verify/fill factual gaps: 영업시간, 주소, 가격)
  → Write                (in the shape of the user's own template)
  → Publish to Naver     (headless) + report
```

**Scout comes before Interview, and that ordering is the whole point.** If you
ask before you know what the place is famous for, you ask the same four questions
every blog asks — 맛이 어땠어요, 얼마였어요, 아쉬운 점은요, 누구랑 갔어요 — and
the one thing worth reading about never makes it into the post.

---

## 0. Setup

1. Read `content/config/brand-voice.md`. If missing, use defaults
   (친근한 전문가, 존댓말, AI 상투어 금지).

2. Read the review templates in `content/config/review-templates/`.
   These are the user's own example posts — they teach **shape only**
   (structure, section rhythm, how it opens and closes, sentence feel).
   Never copy their sentences; the content comes from this trip/meal/product.

   **Read only the templates that apply to this review's type.** A filename
   prefixed with a type (`맛집-…`) is scoped to that type — do not let a 맛집
   example shape a 제품 review. Unprefixed files apply to every type. You won't
   know the type until Step 1 classifies it, so do this read after that.

   If the directory is empty or missing, mention it once and move on:
   > 참고할 후기 예시가 없어서 기본 구조로 씁니다. 예시를 주시면 그 양식으로 맞춰 드려요.

   Don't block on it, and don't write a "skipped" marker to suppress the notice —
   a marker written during one run would silently prevent the user from ever
   being offered the option again, which is worse than mentioning it each time.
   If the user hands you example posts at any point, write them to
   `content/config/review-templates/<type>-<slug>.md` and use them from then on.

3. Locate the photos. The user gives a folder path (or drags files in). Glob it
   for `*.jpg *.jpeg *.png *.heic *.webp`. If no photos are found, tell the user
   and ask for the path — do not proceed photoless.

4. Check the photo set against what a post actually needs:

   | | 최소 | 왜 |
   |---|---|---|
   | 가게 외관 | 1장 | 독자가 찾아갈 때 보는 것. 간판·입구 |
   | 음식 | 3장 | 한 장이면 "사진→짧은글" 리듬이 안 나온다 |
   | 주차 | 1장 | 주차장, **가게 주차가 안 되면 근처 공영주차장 네이버지도 캡처** |

   This is the whole reason the diary rhythm exists — one photo collapses it, and
   the post comes out as a compressed summary instead. Read `brand-voice.md`'s
   photo-rhythm note if you need convincing.

   **If the set is short, ask once — naming exactly what's missing.** Then take
   whatever answer you get:

   > 사진이 음식 1장뿐이네요. 외관 1장 · 음식 2장 더 · 주차 1장 있으면 일기형으로
   > 제대로 씁니다. 있으면 주세요. 없으면 지금 걸로 갑니다.

   If the user says they don't have more, **proceed with what you have** — do not
   block, do not nag twice, do not re-ask on the next stage. Write the shorter
   post honestly, and note the missing photos in `todo.md` so a future run can
   redo it properly.

   **Never compensate for a missing photo with prose.** No invented 외관 description,
   no "주차장은 이랬어요" written from the user's one-line memory. Fewer photos means
   a shorter post, not a padded one.

---

## 1. Read the photos — extract facts before asking anything

**Read every photo with the Read tool.** They are evidence, not decoration.
Pull out every hard fact visible:

- 간판·메뉴판 → 상호명, 메뉴 이름, **가격**
- 영수증 → 날짜, 총액, 주문 내역, 지점명
- 음식 사진 → 요리 종류, 플레이팅, 양
- 풍경·건물 → 장소, 날씨, 시간대(낮/밤), 계절
- 제품 → 브랜드, 모델명, 구성품
- 사람 많음/적음 → 웨이팅·혼잡도 단서

Then classify the **review type** from the photos + description:
`맛집` · `여행` · `제품` · `장소`. Read the matching question set at
`content/config/review-types/<type>.md`. If none matches, use `맛집` as the
closest shape and adapt.

---

## 2. Scout — find out what this place is known for (BEFORE you ask anything)

Search the web for the place/product **before** the interview. You are not
gathering facts for the post yet — you are finding out **what makes this place
distinctive**, so you know what's worth asking about.

> 규카츠 이치니산: 소스를 주지 않고 와사비·간장·암염으로 먹는다. 레어로 튀겨 나와
> 손님이 1인용 돌판 화로에 직접 구워 먹는다. 좌석 11석.

That's the thing a reader wants to hear about, and **only the user can tell you
how it actually went.** If you interview before scouting, you don't know it
exists, and you end up asking "맛이 어땠어요?" like every other blog.

This is the step that was missing, and it caused a real failure: the interview
skipped the sauce entirely, the post got written without it, and the user had to
catch it afterwards.

Write what you find into `research.md` (you'll add the factual stuff — 영업시간,
주소 — in Step 4).

---

## 3. Interview — ask what only the user can answer

Take the question set for this review type, subtract everything you already know
(from the photos + the user's description), and ask what's left. Never ask
something a photo already answers — if the menu board shows 트러플 파스타
24,000원, you do not ask what they ate or what it cost.

**Lead with the distinctive thing you found while scouting.** Ask how the
signature experience actually went — 직접 구워 먹는 게 어땠는지, 소스 없이 먹는 게
어땠는지, 그 전망대의 일몰이 어땠는지. This question is the difference between a
review and a generic "맛있었어요" post, and it is the one you are most likely to
drop, because the generic checklist questions crowd it out.

Then fill in the rest: 아쉬운 점 (always — a review with no downside reads as an
ad), 가격/메뉴 if the photos don't show it, 동행·분위기, 웨이팅.

Use `AskUserQuestion` and batch them. Two rounds is fine — one for the
distinctive stuff, one to fill gaps. Offer likely options so the user can tap
instead of type, but make sure your options are grounded in what you scouted
(don't offer "소스 중 뭐가 좋았나요" at a place that serves no sauce).

Never defer the signature question to `todo.md`. Anything the user could have
told you in 10 seconds should be asked now, not left as a hole in the post.

Always end the round with a free-form opening:
> 이 외에 꼭 글에 들어갔으면 하는 게 있나요? (없으면 넘어갈게요)

Now pick the post slug from the subject (가게명·장소명·제품명 — not the
category), and create the folder:

```
content/reviews/<YYYY-MM-DD>-<slug>/
```

Copy the photos into `<folder>/photos/`, renamed in shooting order
(`01-간판.jpg`, `02-메뉴판.jpg`, …) so the writer can place them by name.

Write `interview.md`: what the photos showed, what the user said, what the user
answered, and an explicit **아직 모르는 것** list.

Resume logic — if the folder already exists:
- `naver.md` exists → skip to Step 6 (publish).
- `research.md` exists → skip to Step 5 (write).
- `interview.md` exists → skip to Step 4 (research).

---

## 4. Research — fill the factual gaps only

For each item in **아직 모르는 것**, run `WebSearch` / `WebFetch`:
영업시간, 정확한 주소, 휴무일, 주차 여부, 가격대, 예약 방법.

Rules:
- Verify, don't harvest. You are confirming the user's experience, not
  rewriting someone else's blog.
- If search does not confirm a fact, **leave it as `[확인 필요: ...]`**.
  Never fill a gap with a plausible guess.
- Do not copy sentences from search results.

Write `research.md` (fact + source URL per line). Skip this step entirely if
nothing is missing.

---

## 5. Write → naver.md

Spawn `review-writer` via Task. Pass:
- `interview.md`, `research.md` (if any)
- `content/config/brand-voice.md`
- `content/config/platforms/naver.md` (제목·SEO·분량 규칙)
- The review templates — **as shape reference only**
- The photo filenames, in order

It returns the full post as text. Write it to `naver.md` yourself, in the exact
format `publish.py` expects:

```markdown
---
title: <제목>
tags: [태그1, 태그2, ...]
---

본문 문단…

[사진: 02-메뉴판.jpg — 트러플 파스타 24,000원]

다음 문단…
```

**`naver.md` is what the public will read. Nothing internal belongs in it.**

Two things follow from that, and they are easy to get wrong:

- **`[확인 필요]` never goes in `naver.md`.** Collect every unresolved item into
  `todo.md` instead, and show that list to the user. A `[확인 필요]` left in the
  body would be published verbatim — the reader would see your unfinished notes.
  If a fact is unresolved, either leave the sentence out or ask the user now.

- **Not every photo belongs in the post.** Place the photos that help a reader —
  간판, 음식, 풍경, 제품. Photos you used purely as *evidence* (영수증, 주차 정산기,
  가격표 메모) have already done their job: you read the facts off them. Leaving
  them out is normal. Never invent a section just to give a photo somewhere to
  live — if you catch yourself writing a "영수증" heading, that's the tell.

Then show the user the draft **and** `todo.md`, and ask whether to publish. This
is the one gate in the pipeline, because Step 5 is irreversible.

---

## 6. Publish → publish-report.md

Publishing is a public, hard-to-undo action. Confirm with the user first
("이대로 발행할까요?"), then run:

```bash
.venv/bin/python scripts/naver/publish.py "content/reviews/<folder>" --blog-id <네이버_아이디>
```

The script is headless and reads `secrets/naver-session.json`. Handle its exit
codes:

- **0** — published. It prints the post URL as JSON.
- **3** — session expired. Tell the user to run
  `python3 scripts/naver/login.py --blog-id <아이디>` once (a browser opens,
  they log in, the session is saved), then re-run `/review` — it resumes at
  publish since `naver.md` already exists. Do NOT try to log in on their behalf.
- **4** — the editor's DOM changed and a selector missed. The script saves a
  screenshot to `<folder>/publish-failure.png`. Read it, report what you see,
  and offer to fix the selector — do not retry blindly.

On success, write `publish-report.md`: 발행 URL, 발행 시각, 제목, 사진 N장,
그리고 `[확인 필요]`로 남은 항목이 있으면 "발행 후 직접 확인 요망"으로 다시 나열.

Then print a summary:

```
✅ 발행 완료: <URL>
   content/reviews/<folder>/
     interview.md  — 사진 판독 + 인터뷰
     research.md   — 검색 보강분
     naver.md      — 발행 본문
     publish-report.md
```

---

## Rules

- **사진이 곧 사실.** 사진에서 읽은 것 > 사용자 설명 > 검색 > (그 외 없음).
- **모르면 묻고, 물어도 모르면 지어내지 않는다.** 미확인 항목은 `todo.md`로
  빼고 본문에서는 그 문장을 빼거나 사용자에게 지금 묻는다. `naver.md` 본문에
  `[확인 필요]`를 남기면 그대로 발행된다.
- **템플릿은 모양만.** 예시 글의 문장을 절대 옮기지 않는다.
- **발행 전 반드시 확인.** 발행은 되돌리기 어렵다.
