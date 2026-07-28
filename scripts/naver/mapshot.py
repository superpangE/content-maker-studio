#!/usr/bin/env python3
"""가게 위치를 지도 이미지로 그려 photos/ 에 넣는다.

네이버 에디터는 임의의 iframe·HTML 임베드를 받지 않는다. 그래서 지도를 '넣는' 게
아니라 '그려서 사진으로 올린다'. 사진 업로드 경로는 이미 있으므로 새로 만들 게 없다.

국내 가게라면 이것보다 네이버 '장소' 카드가 낫다 (검색 노출에 유리하다).
publish.py 의 frontmatter `place:` 를 쓰면 된다. 이 스크립트는 네이버 장소 DB 에
없는 해외 가게용이다.

지도 타일은 OpenStreetMap 을 쓴다. 구글맵 캡처는 이용약관이 걸리고, OSM 은
출처만 밝히면 된다 — 캡션에 자동으로 넣는다.

    python3 scripts/naver/mapshot.py "牛かつ 壱弐参 秋葉原" \
        --out content/reviews/<폴더>/photos/02-지도.jpg
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

NOMINATIM = "https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1"
# Nominatim 은 User-Agent 를 요구한다. 없으면 403.
UA = "content-maker-studio/1.0 (personal blog tooling)"

PAGE = """
<!doctype html><meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html,body{margin:0}
  #map{width:%(w)dpx;height:%(h)dpx}
  .leaflet-control-attribution{font-size:11px}
</style>
<div id="map"></div>
<script>
  const map = L.map('map', {zoomControl:false, attributionControl:true})
                .setView([%(lat)f, %(lon)f], %(zoom)d);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',
              {attribution:'© OpenStreetMap'}).addTo(map);
  L.marker([%(lat)f, %(lon)f]).addTo(map);
  map.whenReady(() => { window.__ready = true; });
</script>
"""


def geocode(api, query: str) -> tuple[float, float, str]:
    """Playwright 의 HTTP 클라이언트로 좌표를 찾는다.

    urllib 대신 이걸 쓰는 이유: 브라우저가 이미 필요하고, 사내 프록시나 샌드박스
    환경에서 파이썬 urllib 만 TLS 검증에 걸려 죽는 경우가 있다. 경로를 하나로 모은다.
    """
    r = api.get(NOMINATIM.format(q=urllib.parse.quote(query)))
    if not r.ok:
        sys.exit(f"지오코딩 실패 (HTTP {r.status}): {query}")
    data = r.json()
    if not data:
        sys.exit(f"위치를 찾지 못했습니다: {query}\n"
                 f"가게 이름 대신 주소로 다시 시도해보세요 (현지어가 정확합니다).")
    hit = data[0]
    return float(hit["lat"]), float(hit["lon"]), hit.get("display_name", "")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("query", help="가게 이름 또는 주소 (현지어가 정확도가 높다)")
    ap.add_argument("--out", type=Path, required=True, help="저장할 이미지 경로")
    ap.add_argument("--zoom", type=int, default=16)
    ap.add_argument("--width", type=int, default=1000)
    ap.add_argument("--height", type=int, default=700)
    args = ap.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright 가 없습니다:\n"
                 "  pip install playwright && python3 -m playwright install chromium")

    args.out.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        api = p.request.new_context(extra_http_headers={"User-Agent": UA})
        lat, lon, name = geocode(api, args.query)
        api.dispose()

        html = PAGE % {"lat": lat, "lon": lon, "zoom": args.zoom,
                       "w": args.width, "h": args.height}
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": args.width, "height": args.height})
        page.set_content(html)
        page.wait_for_function("window.__ready === true", timeout=15000)
        page.wait_for_timeout(2500)  # 타일이 다 그려질 때까지
        page.locator("#map").screenshot(path=str(args.out), type="jpeg", quality=90)
        browser.close()

    print(json.dumps(
        {"out": str(args.out), "lat": lat, "lon": lon, "matched": name,
         "caption": "지도: © OpenStreetMap"},
        ensure_ascii=False, indent=2,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
