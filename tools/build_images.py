"""원본 이미지 → static/img/*.webp (풀 1400px + 썸네일 600px).
usage: python tools/build_images.py <korea_photo_dir> <car_photo_dir>
"""
import sys, os
from PIL import Image, ImageOps

OUT = os.path.join(os.path.dirname(__file__), "..", "static", "img")
os.makedirs(OUT, exist_ok=True)

# (원본 파일명, 출력 이름)
KOREA = [
    ("한국 여행 이미지.jpg", "gyeongbokgung-guard"),
    ("한국여행 이미지2.jpg", "hangang-night"),
    ("한국여행 이미지4.jpg", "bukhansan-view"),
    ("한국여행이미지3.jpg", "lotte-tower-night"),
    ("한국여행이미지5.jpg", "namsan-tower-winter"),
    ("한국여행이미지6.jpg", "namsan-sunset"),
    ("한국여행이미지7.jpg", "namsan-moon"),
    ("한국여행이미지8.jpg", "gwanghwamun-snow"),
    ("한국여행이미지9.jpg", "seoul-night-skyline"),
]
ILLUST = [(f"여행객들 AI 이미지 ({i}).jpg", f"memory-{i:02d}") for i in range(1, 15)] + [
    ("히어로2.jpg", "illust-hero"),
    ("히어로.jpg", "illust-welcome"),
    ("중단.jpg", "illust-seoul"),
    ("연락처.jpg", "illust-contact"),
]
CARS = [
    ("staria-limo.jpg", "staria-limo"),
    ("쏠라티.jpg", "solati"),
    ("제네시스 vip 탑승차량.jpg", "genesis-vip"),
]


def save(im, name, width, suffix=""):
    im = im.copy()
    im.thumbnail((width, width * 2))
    im.save(os.path.join(OUT, f"{name}{suffix}.webp"), "WEBP", quality=82, method=6)


def build(src_dir, items):
    for fname, name in items:
        im = ImageOps.exif_transpose(Image.open(os.path.join(src_dir, fname))).convert("RGB")
        save(im, name, 1400)
        save(im, name, 600, "-thumb")
        print(name, im.size)


if __name__ == "__main__":
    build(sys.argv[1], KOREA)
    build(sys.argv[1], ILLUST)
    build(sys.argv[2], CARS)
    make_og(sys.argv[1])


def make_og(src_dir):
    """OG 1200x630: 왼쪽 브랜드 문구 + 오른쪽 히어로 일러스트 전체."""
    from PIL import ImageDraw, ImageFont
    W, H = 1200, 630
    og = Image.new("RGB", (W, H))
    top, bot = (191, 228, 255), (255, 246, 230)  # 하늘색 → 크림 (사이트 히어로와 동일)
    for y in range(H):
        k = y / H
        ImageDraw.Draw(og).line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * k) for a, b in zip(top, bot)))
    ill = ImageOps.exif_transpose(Image.open(os.path.join(src_dir, "히어로2.jpg"))).convert("RGB")
    ill = ImageOps.fit(ill, (550, 550))
    frame = Image.new("RGB", (570, 570), "white"); frame.paste(ill, (10, 10))
    og.paste(frame, (W - 570 - 40, (H - 570) // 2))
    d = ImageDraw.Draw(og)
    font = lambda w, size: ImageFont.truetype(f"C:/Windows/Fonts/YuGoth{w}.ttc", size)  # ponytail: Windows 전용 빌드 도구
    ink, pink = (58, 46, 42), (232, 84, 120)
    d.text((60, 120), "KUMA TRAVEL", font=font("B", 26), fill=pink)
    d.text((56, 160), "クマトラベル", font=font("B", 72), fill=ink)
    d.text((60, 262), "韓国・ソウル 日本語OK", font=font("B", 34), fill=ink)
    d.text((60, 308), "プライベート空港送迎・貸切", font=font("B", 34), fill=ink)
    d.rounded_rectangle((56, 390, 520, 470), radius=40, fill=(255, 212, 92))
    d.text((84, 408), "仁川⇄ソウル 150,000ウォン", font=font("B", 32), fill=ink)
    d.text((60, 500), "往復予約で10%OFF  ♥  LINEで予約", font=font("M", 26), fill=pink)
    og.save(os.path.join(OUT, "og.jpg"), "JPEG", quality=88)
    print("og", og.size)
