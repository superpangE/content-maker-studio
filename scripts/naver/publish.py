#!/usr/bin/env python3
"""후기 폴더(naver.md + photos/)를 네이버 블로그에 발행한다.

headless 로 돌기 때문에 로컬과 클라우드에서 같은 코드가 동작한다.
로그인은 하지 않는다 — login.py 가 만들어 둔 세션 파일만 읽는다.

    python3 scripts/naver/publish.py content/reviews/2026-07-13-어느가게 --blog-id <아이디>

종료 코드
    0  발행 성공 (stdout 에 {"url": ...} JSON)
    1  입력이 잘못됨 (폴더·naver.md 없음, 형식 오류)
    2  세션 파일 없음 → login.py 먼저
    3  세션 만료 → login.py 다시
    4  에디터 DOM 이 바뀌어 선택자가 빗나감 (스크린샷 남김)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

WRITE_URL = "https://blog.naver.com/{blog_id}?Redirect=Write"
DEFAULT_SESSION = Path("secrets/naver-session.json")
# 캡션 구분자는 "공백 + 대시 + 공백" 일 때만 인정한다.
# 그러지 않으면 파일명 안의 하이픈(01-간판.jpg)을 구분자로 착각해 "01" 로 잘린다.
PHOTO_RE = re.compile(r"^\[사진:\s*(?P<file>.+?)(?:\s+[—–-]\s+(?P<caption>.*?))?\s*\]$")

# 스마트에디터 ONE. 네이버가 클래스명을 자주 바꾸므로 후보를 순서대로 시도한다.
# 여기서 실패하면 exit 4 + 스크린샷 — 이 목록만 고치면 된다.
SEL = {
    "editor_frame": ["#mainFrame"],
    # 주의: 여기에 "button:has-text('취소')" 를 넣으면 안 된다.
    # has-text 는 부분 문자열 매칭이라 팝업이 없을 때 툴바의 '취소선' 버튼을 눌러버리고,
    # 그러면 글 전체가 취소선으로 발행된다. 팝업 전용 클래스만 쓴다.
    "restore_popup_cancel": [".se-popup-button-cancel"],
    "help_popup_close": [
        ".se-help-panel-close-button",
        ".se-popup-close-button",
    ],
    "title": [
        ".se-section-documentTitle .se-text-paragraph",
        ".se-documentTitle .se-text-paragraph",
    ],
    "body": [
        ".se-section-text .se-text-paragraph",
        ".se-component-content .se-text-paragraph",
    ],
    "image_button": [
        "button.se-image-toolbar-button",
        "button[data-name='image']",
        "button[title='사진']",
    ],
    # 장소 카드. 해외 장소면 네이버가 구글 Static Maps 로 그려준다
    # (se-placesMap → maps.googleapis.com/maps/api/staticmap).
    # 그래서 '구글맵을 넣는' 방법은 iframe 이 아니라 이 컴포넌트다.
    "place_button": [
        "button:has-text('장소')",
        "button[data-name='place']",
    ],
    # 국내/해외 전환. 기본이 '국내'라서 해외 가게는 여기서 안 바꾸면 결과가 0건이다.
    "place_region": [".se-popup-button-map-place"],
    "place_region_option": [".se-popup-select-option-item.se-map-place-item"],
    # react-autosuggest 라서 fill() 로 값을 꽂으면 onChange 가 안 돌아 검색이 안 된다.
    # 반드시 키보드로 실제 타이핑해야 한다.
    "place_input": ["input.react-autosuggest__input"],
    "place_search": [".se-place-search-button"],
    "place_result": [".se-place-map-search-result-item"],
    "place_add": [".se-place-add-button"],
    "place_confirm": ["button:has-text('확인')"],
    "publish_open": [
        "button:has-text('발행')",
        ".publish_btn__m9KHH",
    ],
    "tag_input": [
        "#tag-input",
        "input[placeholder*='태그']",
    ],
    "publish_confirm": [
        ".confirm_btn__WEaBq",
        "button[data-testid='seOnePublishBtn']",
    ],
}


@dataclass
class Post:
    title: str
    tags: list[str]
    blocks: list[tuple[str, str]]   # ("text", 문단) | ("photo", 파일경로)
    captions: dict[str, str]        # 파일명 → 캡션
    place: str = ""                 # 장소 카드로 붙일 검색어 (비면 안 붙인다)
    place_region: str = "국내"       # 장소 검색 범위. 해외 가게는 "해외" 로.


def die(code: int, msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(code)


def parse_post(folder: Path) -> Post:
    md = folder / "naver.md"
    if not md.is_file():
        die(1, f"naver.md 가 없습니다: {md}")

    raw = md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        die(1, "naver.md 앞머리에 --- title/tags --- 블록이 없습니다.")
    front, body = m.group(1), m.group(2)

    title = ""
    place = ""
    region = "국내"
    tags: list[str] = []
    for line in front.splitlines():
        if line.startswith("title:"):
            title = line.split(":", 1)[1].strip()
        elif line.startswith("place_region:"):
            region = line.split(":", 1)[1].strip()
        elif line.startswith("place:"):
            place = line.split(":", 1)[1].strip()
        elif line.startswith("tags:"):
            tags = [t.strip() for t in line.split(":", 1)[1].strip(" []").split(",") if t.strip()]
    if not title:
        die(1, "naver.md 에 title 이 없습니다.")

    # 미완성 메모가 본문에 남아 있으면 발행하지 않는다.
    # 이건 발행되면 독자가 그대로 읽는다 — 되돌리기 어려우니 여기서 막는다.
    if "[확인 필요" in body or "=== 확인 필요 ===" in body:
        die(1, "본문에 '[확인 필요]' 가 남아 있습니다. 발행하지 않았습니다.\n"
               "확인된 내용으로 채우거나 그 문장을 빼고, 미확인 항목은 todo.md 로 옮기세요.")

    blocks: list[tuple[str, str]] = []
    captions: dict[str, str] = {}
    for chunk in (c.strip() for c in body.split("\n\n")):
        if not chunk:
            continue
        photo = PHOTO_RE.match(chunk)
        if photo:
            name = photo.group("file").strip()
            path = folder / "photos" / name
            if not path.is_file():
                die(1, f"사진 파일이 없습니다: {path}")
            blocks.append(("photo", str(path)))
            captions[name] = (photo.group("caption") or "").strip()
        else:
            blocks.append(("text", chunk))

    if not blocks:
        die(1, "naver.md 본문이 비어 있습니다.")
    return Post(title=title, tags=tags, blocks=blocks, captions=captions,
                place=place, place_region=region)


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(s: str) -> str:
    """굵게·기울임만 HTML 로."""
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", s)
    return s


def md_to_html(text: str) -> str:
    """마크다운 문단을 HTML 로 바꾼다.

    스마트에디터 ONE 에는 HTML 소스 편집 모드가 없다. 대신 클립보드에 text/html 을
    담아 붙여넣으면 에디터가 그걸 파싱해서 자기 컴포넌트(소제목·굵게·목록)로
    변환해준다. 그래서 'HTML 을 넣는' 게 아니라 'HTML 을 붙여넣어 변환시킨다'.
    """
    html, bullets = [], []

    def flush():
        if bullets:
            html.append("<ul>" + "".join(f"<li>{b}</li>" for b in bullets) + "</ul>")
            bullets.clear()

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        h = re.match(r"^(#{1,6})\s+(.*)$", line)
        b = re.match(r"^[-*+]\s+(.*)$", line)
        if h:
            flush()
            level = min(len(h.group(1)) + 1, 4)  # # → h2 (네이버는 h1 을 안 쓴다)
            html.append(f"<h{level}>{inline(h.group(2))}</h{level}>")
        elif b:
            bullets.append(inline(b.group(1)))
        else:
            flush()
            html.append(f"<p>{inline(line)}</p>")
    flush()
    return "".join(html)


PREVIEW_CSS = """
body{margin:0;background:#eaeaea;font-family:-apple-system,'Apple SD Gothic Neo',sans-serif}
.wrap{max-width:740px;margin:24px auto;background:#fff;padding:48px 44px 64px;
      box-shadow:0 1px 4px rgba(0,0,0,.12)}
h1{font-size:28px;line-height:1.4;margin:0 0 8px;color:#1a1a1a}
.meta{color:#999;font-size:13px;padding-bottom:24px;border-bottom:1px solid #eee;margin-bottom:32px}
h2,h3,h4{font-size:20px;margin:38px 0 14px;color:#1a1a1a;line-height:1.5}
p{font-size:16px;line-height:1.9;color:#333;margin:0 0 18px}
b{font-weight:700;color:#111}
img{max-width:100%;display:block;margin:28px auto;border-radius:2px}
figcaption{text-align:center;color:#999;font-size:13px;margin:-18px 0 28px}
.tags{margin-top:44px;padding-top:24px;border-top:1px solid #eee}
.tag{display:inline-block;color:#0f8a4f;font-size:14px;margin:0 10px 8px 0}
.place{border:1px solid #e5e5e5;border-radius:6px;padding:18px 20px;margin:32px 0;
       background:#fafafa;font-size:15px;color:#333}
.place div{color:#999;font-size:13px;margin-top:6px}
.note{max-width:740px;margin:0 auto 16px;padding:10px 14px;background:#fff8dc;
      border-left:3px solid #e0b400;font-size:13px;color:#665500}
"""


def write_preview(folder: Path, post: "Post") -> Path:
    """발행될 모습을 HTML 로 그려 둔다. 계정 없이도 확인할 수 있다.

    발행에 쓰는 md_to_html 을 그대로 쓴다 — 미리보기와 실제 결과가 갈라지면
    미리보기의 의미가 없다.
    """
    parts = []
    for kind, value in post.blocks:
        if kind == "text":
            parts.append(md_to_html(value))
        else:
            name = Path(value).name
            cap = post.captions.get(name, "")
            parts.append(f'<img src="photos/{name}" alt="">')
            if cap:
                parts.append(f"<figcaption>{esc(cap)}</figcaption>")
    if post.place:
        parts.append(
            f'<div class="place"><b>📍 {esc(post.place)}</b>'
            f'<div>네이버 장소 카드가 여기 들어갑니다 — 지도·주소·길찾기. '
            f'해외 장소는 네이버가 구글맵으로 그려줍니다.</div></div>'
        )
    tags = "".join(f'<span class="tag">#{esc(t)}</span>' for t in post.tags)
    html = (
        f"<!doctype html><meta charset='utf-8'><title>{esc(post.title)}</title>"
        f"<style>{PREVIEW_CSS}</style>"
        f"<div class='note'>미리보기입니다. 실제 발행에 쓰는 변환기로 그렸으니 "
        f"올라갈 모습과 같습니다. 사진 위치·소제목·굵기를 확인하세요.</div>"
        f"<div class='wrap'><h1>{esc(post.title)}</h1>"
        f"<div class='meta'>네이버 블로그 미리보기 · 사진 "
        f"{sum(1 for k, _ in post.blocks if k == 'photo')}장</div>"
        + "".join(parts)
        + f"<div class='tags'>{tags}</div></div>"
    )
    out = folder / "preview.html"
    out.write_text(html, encoding="utf-8")
    return out


def plain(text: str) -> str:
    """클립보드가 막혔을 때 쓰는 폴백 — 마크다운 기호를 벗겨 맨 텍스트로."""
    out = []
    for line in text.splitlines():
        line = re.sub(r"^\s{0,3}#{1,6}\s+", "", line)
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        line = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"\1", line)
        line = re.sub(r"^\s{0,3}[-*+]\s+", "· ", line)
        out.append(line)
    return "\n".join(out)


def find(scope, names: list[str], timeout: int = 5000):
    """후보 선택자를 순서대로 시도한다. 다 빗나가면 None."""
    for sel in names:
        loc = scope.locator(sel).first
        try:
            loc.wait_for(state="visible", timeout=timeout)
            return loc
        except Exception:
            continue
    return None


def dismiss(scope, names: list[str]) -> None:
    """있으면 닫고, 없으면 그냥 넘어가는 팝업들."""
    loc = find(scope, names, timeout=2000)
    if loc:
        try:
            loc.click()
        except Exception:
            pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path, help="후기 폴더 (naver.md + photos/)")
    ap.add_argument("--blog-id", required=True)
    ap.add_argument("--session", type=Path, default=DEFAULT_SESSION)
    ap.add_argument("--dry-run", action="store_true", help="파싱만 하고 발행하지 않는다")
    ap.add_argument("--preview", action="store_true",
                    help="발행될 모습을 preview.html 로 그린다 (계정·브라우저 불필요)")
    args = ap.parse_args()

    if not args.folder.is_dir():
        die(1, f"폴더가 없습니다: {args.folder}")

    post = parse_post(args.folder)
    photos = sum(1 for kind, _ in post.blocks if kind == "photo")

    if args.preview:
        out = write_preview(args.folder, post)
        print(json.dumps({"preview": str(out), "title": post.title, "photos": photos},
                         ensure_ascii=False, indent=2))
        return 0

    if args.dry_run:
        print(json.dumps(
            {"title": post.title, "tags": post.tags, "blocks": len(post.blocks), "photos": photos},
            ensure_ascii=False, indent=2,
        ))
        return 0

    if not args.session.is_file():
        die(2, f"세션이 없습니다: {args.session}\n먼저: python3 scripts/naver/login.py --blog-id {args.blog_id}")

    # 브라우저는 실제로 발행할 때만 필요하다. --dry-run 은 playwright 없이도 돈다.
    try:
        from playwright.sync_api import TimeoutError as PWTimeout
        from playwright.sync_api import sync_playwright
    except ImportError:
        die(1, "playwright 가 없습니다:\n"
               "  pip install playwright && python3 -m playwright install chromium")

    shot = args.folder / "publish-failure.png"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(storage_state=str(args.session), locale="ko-KR")
        # 서식 붙여넣기용. 막히면 맨 텍스트 타이핑으로 폴백한다.
        try:
            ctx.grant_permissions(["clipboard-read", "clipboard-write"],
                                  origin="https://blog.naver.com")
        except Exception:
            pass
        page = ctx.new_page()
        page.goto(WRITE_URL.format(blog_id=args.blog_id))
        page.wait_for_load_state("networkidle")

        if "nid.naver.com" in page.url:
            browser.close()
            die(3, f"세션이 만료됐습니다.\n다시: python3 scripts/naver/login.py --blog-id {args.blog_id}")

        frame = page.frame_locator(SEL["editor_frame"][0])

        def fail(what: str) -> None:
            page.screenshot(path=str(shot), full_page=True)
            browser.close()
            die(4, f"에디터에서 '{what}' 를 찾지 못했습니다. 스크린샷: {shot}\n"
                   f"네이버가 DOM 을 바꿨을 수 있습니다. publish.py 의 SEL 을 고치세요.")

        # 이어쓰기 팝업 / 도움말 패널이 뜨면 치운다.
        dismiss(frame, SEL["restore_popup_cancel"])
        dismiss(frame, SEL["help_popup_close"])

        title = find(frame, SEL["title"])
        if not title:
            fail("제목 입력란")
        title.click()
        page.keyboard.type(post.title, delay=20)

        body = find(frame, SEL["body"])
        if not body:
            fail("본문 입력란")
        body.click()

        paste_key = "Meta+V" if sys.platform == "darwin" else "Control+V"

        def paste_rich(md: str) -> bool:
            """서식(소제목·굵게)을 살려 붙여넣는다. 클립보드가 막히면 False."""
            try:
                page.evaluate(
                    """async (html) => {
                        await navigator.clipboard.write([new ClipboardItem({
                            'text/html': new Blob([html], {type: 'text/html'}),
                            'text/plain': new Blob([html.replace(/<[^>]+>/g, '')],
                                                   {type: 'text/plain'}),
                        })]);
                    }""",
                    md_to_html(md),
                )
                page.keyboard.press(paste_key)
                page.wait_for_timeout(600)
                return True
            except Exception:
                return False

        for kind, value in post.blocks:
            if kind == "text":
                if not paste_rich(value):
                    page.keyboard.type(plain(value), delay=8)
                # 문단 사이를 넉넉히 띄운다. 네이버 후기 글은 빽빽하면 안 읽힌다.
                page.keyboard.press("Enter")
                page.keyboard.press("Enter")
            else:
                btn = find(frame, SEL["image_button"])
                if not btn:
                    fail("사진 첨부 버튼")
                with page.expect_file_chooser() as fc:
                    btn.click()
                fc.value.set_files(value)
                # 업로드가 에디터에 반영될 때까지 기다린다.
                page.wait_for_timeout(3000)
                page.keyboard.press("End")
                page.keyboard.press("Enter")
                page.keyboard.press("Enter")

        # 장소 카드 (frontmatter place:). 글 끝에 붙인다.
        # 해외 장소면 네이버가 구글 Static Maps 로 그려주므로, 이게 곧 '구글맵 넣기'다.
        if post.place:
            btn = find(frame, SEL["place_button"])
            if not btn:
                fail("장소 버튼")
            btn.click()
            page.wait_for_timeout(1500)

            # 검색 범위. 기본이 '국내' 라 해외 가게는 여기서 안 바꾸면 0건이 나온다.
            region = find(frame, SEL["place_region"])
            if region and region.inner_text().strip() != post.place_region:
                region.click()
                page.wait_for_timeout(600)
                opt = frame.locator(SEL["place_region_option"][0], has_text=post.place_region).first
                opt.click()
                page.wait_for_timeout(600)

            box = find(frame, SEL["place_input"])
            if not box:
                fail("장소 검색창")
            box.click()
            # fill() 은 쓰지 않는다 — react-autosuggest 가 onChange 를 못 받아 검색이 안 된다.
            page.keyboard.type(post.place, delay=60)
            page.wait_for_timeout(600)
            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)

            hit = find(frame, SEL["place_result"])
            if not hit:
                # 조용히 넘어가면 지도 없는 글이 발행된다. 멈추고 알린다.
                fail(f"장소 검색 결과 ('{post.place}', 범위: {post.place_region})")

            # '추가' 버튼은 항목에 마우스를 올려야 나타난다. hover 없이는 클릭이 안 된다.
            hit.hover()
            page.wait_for_timeout(400)
            add = find(frame, SEL["place_add"])
            if not add:
                fail("장소 추가 버튼")
            add.click()
            page.wait_for_timeout(1500)

            ok = find(frame, SEL["place_confirm"])
            if not ok or ok.is_disabled():
                fail("장소 확인 버튼 (선택이 안 된 상태)")
            ok.click()
            page.wait_for_timeout(2500)

        # 발행 패널 열기 → 태그 → 발행
        open_btn = find(page, SEL["publish_open"]) or find(frame, SEL["publish_open"])
        if not open_btn:
            fail("발행 버튼")
        open_btn.click()

        if post.tags:
            tag_input = find(page, SEL["tag_input"]) or find(frame, SEL["tag_input"])
            if tag_input:
                tag_input.click()
                for tag in post.tags:
                    page.keyboard.type(tag, delay=20)
                    page.keyboard.press("Enter")

        confirm = find(page, SEL["publish_confirm"]) or find(frame, SEL["publish_confirm"])
        if not confirm:
            fail("발행 확인 버튼")
        confirm.click()

        # 발행되면 글 페이지로 넘어간다.
        try:
            page.wait_for_url(re.compile(r"blog\.naver\.com/.+"), timeout=30000)
            page.wait_for_load_state("networkidle")
        except PWTimeout:
            fail("발행 후 이동 (발행이 안 됐을 수 있습니다)")

        url = page.url
        browser.close()

    print(json.dumps(
        {"url": url, "title": post.title, "photos": photos, "tags": post.tags},
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
