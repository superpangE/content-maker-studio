# Shorts Visual Style

> 모든 쇼츠 영상이 따르는 비주얼 정체성. 이 파일은 Veo(text-to-video) 프롬프트의
> **공통 베이스**가 된다. shot-designer가 장면별 프롬프트를 만들 때 이 규칙을
> 앞에 깔고 장면 고유 내용을 덧붙인다.
> `/setup-content`(향후 확장)로 갱신하거나 직접 편집하세요. 아래는 기본값입니다.

## 비주얼 방향

**일관된 그래픽 / 모션그래픽.** 실사 푸티지가 아니라, 깔끔한 모션그래픽으로
정보를 전달한다. 채널 정체성이 영상마다 유지되도록 색·타이포·모션 규칙을 고정한다.

## 포맷 (고정)

- **종횡비**: 9:16 세로
- **해상도**: 1080 x 1920
- **프레임레이트**: 30fps
- **세이프존**: 상단 220px(플랫폼 UI), 하단 320px(캡션·CTA UI) 안에 핵심 정보·자막 배치 금지 → 중앙 1080x1380 영역에 핵심 시각 요소를 둔다

## 색 팔레트

- **배경**: 딥 네이비 (#0E1525) 또는 차분한 다크 그레이 (#15171C)
- **메인 액센트**: 선명한 시안/블루 (#2FB8FF)
- **보조 액센트**: 옐로우 (#FFD24A) — 강조 숫자·키워드에만
- **텍스트**: 화이트 (#FFFFFF), 보조 텍스트 라이트 그레이 (#B8C0CC)
- 한 영상 안에서 액센트는 2색 이내로 제한 → 일관성 유지

## 타이포그래피

- **폰트 느낌**: 두껍고 둥근 산세리프 (Pretendard / Noto Sans KR Bold 류)
- **자막 위치**: 화면 중앙~하단 1/3, 세이프존 안
- **자막 스타일**: 큰 굵은 글씨 + 반투명 어두운 박스 또는 외곽선 → 가독성 우선
- **강조**: 핵심 숫자·키워드는 옐로우 액센트 + 살짝 키우기 (pop)

## 모션 규칙

- **전환**: 빠르고 깔끔한 컷·슬라이드·스케일. 0.2~0.4초. 화려한 3D 전환 금지
- **요소 등장**: 텍스트·도형은 페이드+슬라이드업 또는 스케일인으로 등장
- **카메라**: 느린 줌인/패럴랙스 정도. 정적이지 않되 과하지 않게
- **리듬**: 내레이션 박자에 맞춰 시각 요소가 바뀐다 (한 문장 = 한 비주얼 비트)

## Veo 프롬프트 공통 베이스 (영문)

shot-designer는 아래 베이스를 모든 장면 프롬프트 앞에 붙인다:

```
Clean 2D motion-graphics style, vertical 9:16 format, deep navy background (#0E1525),
bright cyan accent (#2FB8FF), bold rounded sans-serif typography, smooth minimal
transitions, high contrast, flat design with subtle depth, professional explainer
aesthetic, no live-action footage, no photorealism.
```

장면 고유 내용(예: "a rising bar chart of vote counts", "a baseball stadium icon
with a glowing number")을 이 베이스 뒤에 자연어로 덧붙인다.

## 금지

- 실사 인물 얼굴 클로즈업 생성 (초상권·진위 리스크)
- 워터마크·로고 모방
- 읽기 어려운 얇은 폰트, 저대비 텍스트
- 세이프존 침범 (상단/하단 UI에 가리는 핵심 정보)
- 한 영상 안에서 스타일이 장면마다 튀는 것 (일관성 최우선)

## 길이·장면 가이드 (공통 기본값)

- 장면(shot) 1개 = 3~6초 (Veo 생성 단위와 정렬)
- 영상 총길이는 플랫폼 프로파일이 결정 (아래 platforms/shorts-*.md)
- 훅(첫 장면)은 3초 이내에 핵심을 던진다
