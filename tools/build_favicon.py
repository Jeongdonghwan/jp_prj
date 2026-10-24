"""templates/bear.svg → static/ 아래 favicon.ico, PNG 아이콘들.
usage: python tools/build_favicon.py   (playwright 필요: SVG 렌더링용)
"""
import io, os
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
STATIC = os.path.join(ROOT, "static")
svg = open(os.path.join(ROOT, "templates", "bear.svg"), encoding="utf-8").read()
svg = svg.replace('width="40" height="40"', 'width="512" height="512"')

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 512, "height": 512})
    pg.set_content(f"<html><body style='margin:0;background:transparent'>{svg}</body></html>")
    bear = Image.open(io.BytesIO(pg.locator("svg").screenshot(omit_background=True))).convert("RGBA")
    b.close()

bear = bear.resize((512, 512), Image.LANCZOS)
bear.resize((192, 192), Image.LANCZOS).save(os.path.join(STATIC, "icon-192.png"))
bear.save(os.path.join(STATIC, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])

# iOS 홈 화면: 투명 배경이 검게 나오므로 크림색 바탕 + 여백
apple = Image.new("RGBA", (180, 180), (255, 244, 204, 255))
apple.alpha_composite(bear.resize((150, 150), Image.LANCZOS), (15, 15))
apple.convert("RGB").save(os.path.join(STATIC, "apple-touch-icon.png"))
print("ok")
