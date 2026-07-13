#!/usr/bin/env python3
"""네이버 세션을 한 번만 만들어 파일로 저장한다.

브라우저가 뜨면 직접 로그인하세요. 로그인이 끝난 걸 감지하면 쿠키를
secrets/naver-session.json 으로 저장하고 종료합니다.

이 스크립트는 아이디·비밀번호를 받지도, 저장하지도, 대신 입력하지도 않습니다.
로그인은 사람이 합니다. 자동 로그인은 네이버가 봇으로 판정해 캡차를 띄우거나
계정을 잠글 수 있습니다.

이렇게 만든 세션 파일 하나면 publish.py 는 로컬에서도 클라우드에서도
headless 로 똑같이 돕니다. 클라우드에 올릴 때는 이 파일을 시크릿으로 주입하세요.

    python3 scripts/naver/login.py --blog-id <네이버아이디>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit(
        "playwright 가 없습니다:\n"
        "  pip install playwright && python3 -m playwright install chromium"
    )

LOGIN_URL = "https://nid.naver.com/nidlogin.login"
# 로그인이 끝났는지 확인하는 곳. 로그인 상태여야만 글쓰기 폼이 열린다.
WRITE_URL = "https://blog.naver.com/{blog_id}?Redirect=Write"
DEFAULT_SESSION = Path("secrets/naver-session.json")
LOGIN_TIMEOUT_MS = 5 * 60 * 1000  # 로그인에 5분 준다 (2차 인증 포함)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--blog-id", required=True, help="네이버 아이디 (블로그 ID)")
    ap.add_argument("--session", type=Path, default=DEFAULT_SESSION)
    args = ap.parse_args()

    args.session.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(locale="ko-KR")
        page = ctx.new_page()
        page.goto(LOGIN_URL)

        print("\n브라우저에서 네이버에 로그인하세요. (2차 인증까지 끝내면 됩니다)")
        print("로그인이 끝나면 자동으로 감지해 저장하고 브라우저를 닫습니다.\n")

        # 로그인 도메인을 벗어나면 로그인이 끝난 것.
        try:
            page.wait_for_url(
                lambda url: "nid.naver.com" not in url,
                timeout=LOGIN_TIMEOUT_MS,
            )
        except Exception:
            print("시간 안에 로그인이 끝나지 않았습니다. 저장하지 않고 종료합니다.")
            browser.close()
            return 1

        # 진짜로 글쓰기 폼이 열리는지 확인한다. 로그인 화면으로 튕기면 실패.
        page.goto(WRITE_URL.format(blog_id=args.blog_id))
        page.wait_for_load_state("networkidle")
        if "nid.naver.com" in page.url:
            print("로그인이 유지되지 않았습니다. 저장하지 않고 종료합니다.")
            browser.close()
            return 1

        ctx.storage_state(path=str(args.session))
        browser.close()

    args.session.chmod(0o600)
    print(f"세션 저장 완료: {args.session}")
    print("이제 publish.py 가 headless 로 발행할 수 있습니다.")
    print("이 파일은 로그인된 계정 그 자체입니다. git 에 올리지 마세요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
