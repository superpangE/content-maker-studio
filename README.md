<p align="center">
  <h1 align="center">Content Maker Studio</h1>
  <p align="center">
    카테고리 하나만 주면 블로그·숏폼이 완성되는 콘텐츠 제작 스튜디오.
    <br />
    Claude Code 세션을 전문 에이전트 팀 + 게이트형 파이프라인으로 운영합니다.
  </p>
</p>

<p align="center">
  <a href="https://docs.anthropic.com/en/docs/claude-code"><img src="https://img.shields.io/badge/built%20for-Claude%20Code-f5f5f5?logo=anthropic" alt="Built for Claude Code"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
</p>

---

## 이게 뭐예요?

한국어 콘텐츠를 **집계(aggregation) 기반**으로 만드는 스튜디오입니다. 카테고리(예: `맛집`, `연예뉴스`, `국내야구`)를 주면 실제 한국어 소스(네이버 뉴스·블로그)를 모아 **하나의 핫한 주제**를 골라 깊게 팝니다. 원문 그대로 베끼지 않은 글로 다시 써서 플랫폼별 발행본까지 만듭니다.

각 단계는 전문 에이전트가 맡고 결과물은 **승인 즉시 파일로 저장**됩니다. 대화가 끊겨도 마지막 저장 단계부터 이어집니다.

- **블로그** — 네이버 블로그 / 티스토리·워드프레스
- **숏폼** — YouTube Shorts / Instagram Reels / TikTok (9:16 세로)

> 한 편의 글/영상 = 한 개의 폴더. 모든 산출물(소스·브리프·초고·발행본)이 함께 모입니다.

---

## 빠른 시작

```bash
git clone https://github.com/superpangE/content-maker-studio.git
cd content-maker-studio
claude
```

Claude Code 세션 안에서:

1. **`/setup-content`** — 브랜드 보이스 + 플랫폼 프로필 + (선택) 형태 example 1회 설정. **먼저 실행**.
2. **`/blog <카테고리>`** — 블로그 한 편을 끝까지 생성.
3. **`/shorts <카테고리>`** — 숏폼 제작 스펙(+선택적 렌더)을 끝까지 생성.

예: `/blog 맛집` · `/shorts 국내야구`

설정을 건너뛰어도 기본값으로 동작하며 `/blog`·`/shorts` 첫 실행 때 형태 example이 없으면 1회 물어봅니다.

---

## 파이프라인

### 블로그

```
/blog <카테고리>
  0. 셋업 확인 (brand-voice, 형태 example) + 포스트 폴더
  1.  소스 수집        (source-collector)    → sources.md
  1.5 주제 선택        (오케스트레이터가 1개 선정)
  2.  브리프           (content-strategist)  → brief.md
  3.  아웃라인         (content-strategist)  → outline.md
  4.  마스터 초고      (blog-writer)         → draft.md
  5.  플랫폼 변환      (seo-editor)          → naver.md / tistory.md
```

목표 깊이: **한 주제로 1,500~2,500자.** 여러 주제를 묶지 않고 하나를 깊게 다룹니다.

### 숏폼

```
/shorts <카테고리>
  0. 셋업 + shorts-style + 형태 example + 플랫폼 프로필
  1.  소스 수집        (source-collector)
  1.5 주제 선택        (오케스트레이터)
  2.  브리프           (content-strategist)  → brief.md
  3.  대본             (script-writer)       → script.md
  4.  스토리보드        (shot-designer)       → storyboard.md + shots.json
  5.  렌더 스크립트     (오케스트레이터)       → produce.sh
```

**2단계 출력.** Layer 1(스펙: `script.md`/`storyboard.md`/`shots.json`)은 **API 키 없이** 항상 생성됩니다. Layer 2(`produce.sh`)는 TTS(ElevenLabs)·영상 생성(Veo) API를 호출해 ffmpeg로 9:16 MP4를 렌더합니다. 키가 없으면 무엇이 필요한지 안내하고 깔끔히 종료합니다.

```bash
export ELEVENLABS_API_KEY=...   # TTS (선택)
export VEO_API_KEY=...          # 영상 생성 (선택)
```

---

## 에이전트

포맷 공통:

| 에이전트 | 담당 | 산출 |
|---|---|---|
| **source-collector** | 네이버 뉴스·블로그에서 원본 소스 수집 | `sources.md` |
| **content-strategist** | 왜/누구에게/어떤 앵글/키워드 + 구조 | `brief.md`, `outline.md` |

블로그 전용:

| 에이전트 | 담당 | 산출 |
|---|---|---|
| **blog-writer** | 플랫폼 무관 마스터 초고 (보이스·흐름) | `draft.md` |
| **seo-editor** | 플랫폼별 변환·최적화 | `naver.md`, `tistory.md` |

숏폼 전용:

| 에이전트 | 담당 | 산출 |
|---|---|---|
| **script-writer** | 세로형 대본 (훅/본문/CTA, 비트) | `script.md` |
| **shot-designer** | 샷별 제작 스펙 (Veo 프롬프트 + 자막 + TTS + 타이밍) | `storyboard.md`, `shots.json` |

별도 디렉터 에이전트는 없습니다. `/blog`·`/shorts` 스킬이 오케스트레이터이며 사용자가 카테고리를 주면 파이프라인이 끝까지 돕니다.

---

## 디렉토리 구조

```text
content/
├── config/
│   ├── brand-voice.md          # 페르소나, 톤, 금지 표현
│   ├── blog-example.md         # 블로그 형태 참고 (구조 + 문체) — 셋업/첫 실행 때 생성
│   ├── shorts-example.md       # 숏폼 형태 참고 (구조 + 문체) — 셋업/첫 실행 때 생성
│   ├── shorts-style.md         # 고정된 모션그래픽 비주얼 아이덴티티 (Veo 기준)
│   └── platforms/
│       ├── naver.md            # 네이버 블로그 변환 규칙
│       ├── tistory.md          # 티스토리/워드프레스(구글 SEO) 규칙
│       ├── shorts-youtube.md   # YouTube Shorts 프로필
│       ├── shorts-reels.md     # Instagram Reels 프로필
│       └── shorts-tiktok.md    # TikTok 프로필
├── posts/
│   └── YYYY-MM-DD-<slug>/       # 블로그 1편 = 1폴더
└── shorts/
    └── posts/
        └── YYYY-MM-DD-<slug>/   # 숏폼 1편 = 1폴더
```

`content/config/`는 버전 관리되어 clone에 포함됩니다(기본값 동봉). 생성된 `content/posts/`·`content/shorts/`는 `.gitignore` 처리되어 **fresh clone은 빈 상태로 시작**합니다.

---

## 설계 원칙

- **파일 = 메모리.** 승인된 단계는 전부 디스크에 있고 대화는 보조입니다.
- **1편 = 1폴더.** 한 글/영상의 모든 산출물이 한곳에 모입니다.
- **마스터 초고 후 변환.** `draft.md`를 한 번(플랫폼 무관) 쓰고 플랫폼별 버전을 파생합니다. 플랫폼마다 본문을 다시 쓰지 않습니다.
- **Example = 형태.** `*-example.md`는 구조와 문체(모양)를 가르치고 주제·사실은 매번 소스에서 새로 옵니다. 한 번 등록해 매 실행 재사용합니다.
- **데이터 기반 플랫폼.** 플랫폼 규칙은 config 파일에, 변환 로직은 seo-editor에. 플랫폼 추가 = 프로필 파일 하나 추가.

자세한 운영 가이드: **[.claude/docs/content-studio.md](.claude/docs/content-studio.md)**

---

## 새 포맷 확장

블로그·숏폼과 같은 패턴으로 새 포맷을 추가합니다:

1. 필요하면 config 추가 (예: `content/config/platforms/<플랫폼>.md`)
2. 새 craft를 맡을 전문 에이전트 추가 (예: `script-writer`)
3. 같은 게이트형 파이프라인을 가진 오케스트레이터 스킬 추가 (예: `/shorts`)
4. `content-strategist` 재사용 — 주제·앵글 결정은 포맷 간 공유

---

## 게임 스튜디오 템플릿 유산

이 프로젝트는 게임 스튜디오 템플릿에서 시작했습니다. 게임용 에이전트(`.claude/agents/*`의 게임 역할), 게임 스킬(`brainstorm`, `design-system` 등), 템플릿, 그리고 `design/` `src/` `production/` 트리가 아직 남아 있지만 **콘텐츠 워크플로에는 사용되지 않습니다.** 참고용으로 남겨둔 것이며 삭제하지 않았습니다. 콘텐츠 작업에는 위에 설명한 콘텐츠 에이전트·스킬만 사용하세요.

---

## License

MIT License. 자세한 내용은 [LICENSE](LICENSE) 참고.
