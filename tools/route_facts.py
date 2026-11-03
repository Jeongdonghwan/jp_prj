"""장소별 공항 거리·시간(OSRM 도로 경로) → seo/places.json (페이지마다 다른 사실 재료)

  python -I tools/route_facts.py
시간은 막힘 없는 도로 기준 최소값이라 페이지에는 "目安·渋滞で変動"으로만 쓴다.
좌표는 각 지역 대표 역·랜드마크.
"""
import json, os, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "seo", "places.json")

AIRPORTS = {"icn_t1": (37.4490, 126.4510), "icn_t2": (37.4688, 126.4337), "gmp": (37.5658, 126.8017)}
# slug: (일본어, 한국어, 대표 지점(일본어), 위도, 경도, 서울 정액 요금 대상)
PLACES = {
    "seoul": ("ソウル", "서울", "ソウル市庁", 37.5663, 126.9779, True),
    "myeongdong": ("明洞", "명동", "明洞駅", 37.5609, 126.9863, True),
    "hongdae": ("弘大", "홍대", "弘大入口駅", 37.5572, 126.9245, True),
    "gangnam": ("江南", "강남", "江南駅", 37.4979, 127.0276, True),
    "dongdaemun": ("東大門", "동대문", "東大門デザインプラザ(DDP)", 37.5663, 127.0092, True),
    "namdaemun": ("南大門", "남대문", "南大門市場", 37.5592, 126.9776, True),
    "jongno": ("鍾路・仁寺洞", "종로·인사동", "仁寺洞", 37.5743, 126.9853, True),
    "euljiro": ("乙支路", "을지로", "乙支路3街駅", 37.5663, 126.9918, True),
    "itaewon": ("梨泰院", "이태원", "梨泰院駅", 37.5345, 126.9946, True),
    "yongsan": ("龍山", "용산", "龍山駅", 37.5299, 126.9648, True),
    "seongsu": ("聖水", "성수", "聖水駅", 37.5446, 127.0559, True),
    "jamsil": ("蚕室", "잠실", "ロッテワールドタワー", 37.5125, 127.1025, True),
    "samseong": ("三成・COEX", "삼성·코엑스", "COEX", 37.5116, 127.0595, True),
    "yeouido": ("汝矣島", "여의도", "汝矣島駅", 37.5216, 126.9243, True),
    "yeongdeungpo": ("永登浦", "영등포", "永登浦駅", 37.5157, 126.9076, True),
    "seoul-station": ("ソウル駅", "서울역", "ソウル駅", 37.5547, 126.9707, True),
    "walkerhill": ("ウォーカーヒル", "워커힐", "グランドウォーカーヒル", 37.5551, 127.1050, True),
    "songdo": ("松島", "송도", "松島セントラルパーク", 37.3925, 126.6390, False),
    "incheon-city": ("仁川市内", "인천 시내", "仁川駅(チャイナタウン)", 37.4765, 126.6168, False),
    "paradise-city": ("パラダイスシティ", "파라다이스시티", "パラダイスシティ", 37.4396, 126.4527, False),
    "unseo": ("雲西", "운서", "雲西駅", 37.4927, 126.4937, False),
    "magok": ("麻谷", "마곡", "麻谷ナル駅", 37.5670, 126.8273, True),
}


def route(a, b):
    u = f"https://router.project-osrm.org/route/v1/driving/{a[1]},{a[0]};{b[1]},{b[0]}?overview=false"
    for _ in range(3):
        try:
            r = json.loads(urllib.request.urlopen(u, timeout=20).read())["routes"][0]
            return round(r["distance"] / 1000, 1), round(r["duration"] / 60)
        except Exception:
            time.sleep(2)
    return None, None


out = {}
for slug, (ja, ko, spot, lat, lng, flat) in PLACES.items():
    d = {"ja": ja, "ko": ko, "spot": spot, "lat": lat, "lng": lng, "seoul_flat": flat}
    for ap, xy in AIRPORTS.items():
        km, mins = route(xy, (lat, lng))
        d[ap] = {"km": km, "min": mins}
        time.sleep(1)  # 공개 서버 예의
    out[slug] = d
    print(slug, d["icn_t1"], d["gmp"])
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
sys.stdout.reconfigure(encoding="utf-8")
print(OUT)
