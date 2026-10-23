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
    # OG 이미지 1200x630 (한강 야경 중앙 크롭)
    og = ImageOps.exif_transpose(Image.open(os.path.join(sys.argv[1], "한국여행 이미지2.jpg"))).convert("RGB")
    og = ImageOps.fit(og, (1200, 630), centering=(0.5, 0.45))
    og.save(os.path.join(OUT, "og.jpg"), "JPEG", quality=85)
    print("og", og.size)
