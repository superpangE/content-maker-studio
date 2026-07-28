# 네이버 블로그 발행

`/review` 파이프라인의 마지막 단계. 로그인과 발행을 분리해서, **로그인은 사람이 한 번**,
**발행은 headless 로 매번** 돌게 만들었다. 그래서 로컬과 클라우드에서 같은 코드가 돈다.

## 설치

```bash
pip install playwright
python3 -m playwright install chromium
```

## 최초 1회 — 세션 만들기

```bash
python3 scripts/naver/login.py --blog-id <네이버아이디>
```

브라우저가 뜨면 직접 로그인한다. 2차 인증까지 끝나면 쿠키가
`secrets/naver-session.json` 으로 저장되고 브라우저가 닫힌다.

이 스크립트는 아이디·비밀번호를 받지도 저장하지도 않는다. 자동 로그인을 넣지 않은 건
네이버가 그걸 봇으로 보고 캡차를 띄우거나 계정을 잠그기 때문이다. 사람이 한 번 하는 게
훨씬 안전하고, 어차피 한 번이면 끝난다.

> `secrets/naver-session.json` 은 **로그인된 계정 그 자체**다. `.gitignore` 에 넣어뒀지만
> 실수로도 공유하지 말 것.

## 발행

```bash
python3 scripts/naver/publish.py content/reviews/<폴더> --blog-id <아이디>
python3 scripts/naver/publish.py content/reviews/<폴더> --blog-id <아이디> --dry-run
```

`--dry-run` 은 브라우저를 띄우지 않고 `naver.md` 파싱 결과만 보여준다 (playwright 없이도 됨).
발행 전에 제목·태그·사진 개수를 확인하는 용도.

### 종료 코드

| 코드 | 뜻 | 할 일 |
|---|---|---|
| 0 | 발행 성공 | stdout 에 `{"url": ...}` |
| 1 | 입력 오류 | `naver.md` 형식·사진 경로 확인 |
| 2 | 세션 파일 없음 | `login.py` 먼저 |
| 3 | 세션 만료 | `login.py` 다시 |
| 4 | 선택자 빗나감 | 아래 참고 |

## 클라우드에서 돌리기

`publish.py` 는 headless 라 서버에서 그대로 돈다. 필요한 건 세션 파일 하나뿐이다.

1. 로컬에서 `login.py` 로 `secrets/naver-session.json` 을 만든다.
2. 그 파일을 클라우드에 시크릿으로 주입한다 (볼륨 마운트든 시크릿 매니저든).
3. `--session` 으로 경로를 넘긴다.

```bash
python3 scripts/naver/publish.py <폴더> --blog-id <아이디> --session /run/secrets/naver-session.json
```

**주의:** 네이버는 IP·기기가 크게 바뀌면 세션을 끊을 수 있다. 로컬(한국)에서 만든 쿠키를
해외 리전 서버에 올리면 특히 그렇다. 그러면 `publish.py` 가 **종료 코드 3** 으로 조용히
멈춘다 — 계정을 건드리지 않고, 글은 `naver.md` 에 그대로 남는다. 세션만 다시 만들어
재발행하면 된다. 가능하면 서버와 가까운 곳에서 로그인해 세션을 만드는 게 오래 간다.

## 선택자가 빗나갔을 때 (종료 코드 4)

네이버 스마트에디터는 클래스명이 자주 바뀐다. 빗나가면 스크립트가 글 폴더에
`publish-failure.png` 스크린샷을 남기고 멈춘다 (반쯤 쓰다 만 글을 발행하지 않는다).

고칠 곳은 `publish.py` 상단의 `SEL` 딕셔너리 하나다. 항목마다 후보 선택자를 리스트로
넣어두면 위에서부터 시도한다 — 새 선택자를 리스트 맨 앞에 추가하면 된다.

> 이 선택자들은 **실제 네이버 계정으로 아직 검증하지 않았다.** 첫 발행은 `--dry-run`
> 으로 파싱을 확인한 뒤, 실제로 한 번 돌려보고 실패하면 스크린샷 보고 `SEL` 을 맞추자.
