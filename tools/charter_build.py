"""대절(貸切チャーター) 키워드·거리 → seo/charter_kw.json, seo/charter_places.json, keywords/구마트래블_대절키워드.xlsx

  python -I tools/charter_build.py           (자동완성 원본 keywords/charter_suggest_raw.json 재사용)
  python -I tools/charter_build.py --fetch   (구글 일본 자동완성을 다시 모은다, 약 2,200회 요청)
키워드 = 구글 자동완성에 실제로 뜬 대절·당일치기 검색어 + 키워드_전체.xlsx 의 대절 조합 키워드.
거리 = 서울시청 → 지역 기준 지점 OSRM 도로 거리(막힘 없는 최소값이라 페이지엔 "目安"으로만 쓴다).
"""
import json, os, re, sys, time, urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(__file__))
RAW = os.path.join(ROOT, "keywords", "charter_suggest_raw.json")
KWJ, PLJ = os.path.join(ROOT, "seo", "charter_kw.json"), os.path.join(ROOT, "seo", "charter_places.json")
XLSX = os.path.join(ROOT, "keywords", "구마트래블_대절키워드.xlsx")
CITY_HALL = (37.5663, 126.9779)


def fetch():
    from airport_suggest import suggest, KANA
    PL = ["ソウル", "韓国", "DMZ", "板門店", "全州", "全州韓屋村", "安東", "河回村", "慶州", "釜山", "南怡島", "加平", "春川", "水原", "水原華城",
          "江陵", "束草", "江華島", "利川", "驪州", "エバーランド", "韓国民俗村", "扶余", "公州", "丹陽", "坡州", "楊平", "平昌", "抱川",
          "大邱", "統営", "麗水", "仁川", "光明洞窟", "プチフランス", "ソウル近郊", "韓国 地方"]
    W = ["貸切", "貸切タクシー", "チャーター", "日帰り", "ハイヤー", "専用車", "ツアー", "観光タクシー", "ソウルから"]
    qs = [f"{p} {w}" for p in PL for w in W] + [f"{p} {w} " for p in PL for w in W[:4]] + [f"{p} " + c for p in PL for c in KANA]
    qs += [f"ソウルから{p}" for p in PL] + [f"ソウルから{p} " for p in PL]
    hits = defaultdict(lambda: {"n": 0, "best": 99, "seed": ""})
    with ThreadPoolExecutor(4) as ex:
        for q, res in ex.map(suggest, qs):
            for r, k in enumerate(res):
                k = " ".join(k.split())
                h = hits[k]
                h["n"] += 1
                h["best"] = min(h["best"], r)
                h["seed"] = h["seed"] or q.strip()
    json.dump([{"kw": k, **v} for k, v in hits.items()], open(RAW, "w", encoding="utf-8"), ensure_ascii=False)


A = r"貸切|貸し切り|チャーター|ハイヤー|専用車|観光タクシー"
B = r"日帰り|ツアー|ソウルから|ソウル から|行き方|アクセス"
SK = r"便|機|風呂|アパート|一軒家|wbc|ポーズ|ブログ|コネスト|セルフ|大統領|富山|釧路|バス|電車|ktx|高速|新幹線|飛行機|フェリー|航空券|羽田|成田|関空|福岡|大阪|東京発|his|地下鉄|時刻表|arex|事件|中止|再開|現在|2026|スタバ|服装|温泉|競技場|格安|添乗員|泊|弾丸|アーリー|釜山 から|釜山から|大邱 から|海南|空港 日帰り|国際 空港 日帰り|インスパイア|パラダイス|ワールドカップ|ちほ|オーバー|アプリ|韓国 語|ハイヤー 韓国|dmz.{0,3}アクセス|先行|早期|アーリー|カード|なし|とは|年齢|国際空港|仁川まで|仁川 終電|荷物|トランジット|名古屋|帯広|関西|セール|ピーチ|宙|スペース|図書館|ヨット|スポーツ|始発|ホテル|釜山発|パス|大橋|スター フィールド"
KO = [("日帰り旅行", "당일치기 여행"), ("までの距離", "까지 거리"), ("までの行き方", "까지 가는 법"), ("からの行き方", "에서 가는 법"), ("まで何時間かかりますか", "까지 몇 시간"), ("へ の ", ""), ("まで", "까지"), ("ソウルから", "서울에서 "), ("ソウル から", "서울에서 "), ("貸切タクシー", "대절택시"), ("貸し切り", "대절"), ("貸切", "대절"), ("チャーター車", "차량대절"), ("チャーター", "차량대절"),
      ("観光タクシー", "관광택시"), ("ハイヤー", "의전차량"), ("専用車", "전용차"), ("タクシー", "택시"), ("日帰りツアー", "당일 투어"), ("日帰り", "당일치기"), ("ツアー", "투어"),
      ("行き方", "가는 법"), ("アクセス", "가는 법"), ("料金", "요금"), ("おすすめ", "추천"), ("日本語", "일본어"), ("観光", "관광"), ("予約", "예약"), ("モデル コース", "추천 코스"),
      ("モデルコース", "추천 코스"), ("時間", "시간"), ("距離", "거리"), ("半日", "반나절"), ("1日", "하루"), ("車", "차"), ("空港", "공항"), ("費用", "비용"), ("日本人", "일본인"),
      ("全州韓屋村", "전주한옥마을"), ("全州", "전주"), ("安東", "안동"), ("河回村", "하회마을"), ("シティ", "시티"), ("慶州", "경주"), ("釜山", "부산"), ("大邱", "대구"), ("南怡島", "남이섬"),
      ("加平", "가평"), ("春川", "춘천"), ("水原華城", "수원화성"), ("水原", "수원"), ("江陵", "강릉"), ("束草", "속초"), ("江華島", "강화도"), ("利川", "이천"), ("陶芸 村", "도예촌"),
      ("驪州アウトレット", "여주아울렛"), ("驪州", "여주"), ("エバーランド", "에버랜드"), ("韓国民俗村", "한국민속촌"), ("扶余", "부여"), ("公州", "공주"), ("丹陽", "단양"),
      ("坡州市", "파주시"), ("坡州", "파주"), ("アウトレット", "아울렛"), ("楊平", "양평"), ("平昌", "평창"), ("抱川", "포천"), ("統営", "통영"), ("麗水", "여수"),
      ("仁川チャイナタウン", "인천차이나타운"), ("仁川", "인천"), ("光明洞窟", "광명동굴"), ("プチフランス", "쁘띠프랑스"), ("板門店", "판문점"), ("dmz", "DMZ"),
      ("(非武装地帯)", "(비무장지대)"), ("ソウル近郊", "서울 근교"), ("ソウル", "서울"), ("韓国", "한국"), ("地方 都市", "지방 도시"), ("地方", "지방"), ("松島", "송도"), ("旅", "여행"), ("現地", "현지"), ("人気", "인기"), ("口コミ", "후기"), ("家族", "가족"), ("サービス", "서비스"), ("日本 人", "일본인"), (" 発", " 출발"), ("発 ", "출발 "), ("見学", "견학"), ("非武装 地帯", "비무장지대"), ("非武装地帯", "비무장지대"), ("安い", "저렴"), ("値段", "가격"), ("申し込み", "신청"), ("個人", "개인"), ("自由 の 家", "자유의 집"), ("プレミアム", "프리미엄 "), ("ロッテ", "롯데 "), (" 市", "시"), ("市", "시"), ("韓屋村", "한옥마을"), ("世界遺産", "세계유산"), ("オプショナル", "옵션 "), ("ナイト", "야간 "), ("華 城", "화성"), ("日本 語", "일본어"), ("ナミソム", "남이섬"), ("駅", "역"), ("アート バレー", "아트밸리"), ("(ヨジュ)", ""), ("タクシー", "택시")]


def ko(k):
    for a, b in KO:
        k = k.replace(a, b)
    return " ".join(k.split())


def route(b):
    u = f"https://router.project-osrm.org/route/v1/driving/{CITY_HALL[1]},{CITY_HALL[0]};{b[1]},{b[0]}?overview=false"
    for _ in range(3):
        try:
            r = json.loads(urllib.request.urlopen(u, timeout=20).read())["routes"][0]
            return round(r["distance"] / 1000, 1), round(r["duration"] / 60)
        except Exception:
            time.sleep(2)
    return None, None


def main():
    if "--fetch" in sys.argv:
        fetch()
    import importlib, charter
    have = {}  # 이미 2,000페이지에 있는 키워드 (공항 가이드·기존 랜딩)
    for r in openpyxl.load_workbook(os.path.join(ROOT, "keywords", "구마트래블_페이지URL_2000.xlsx"))["페이지 URL 2000"].iter_rows(min_row=2, values_only=True):
        for k in [r[1]] + (r[9] or "").split(" / "):
            have[k] = r[4]
    rows = {}
    for x in json.load(open(RAW, encoding="utf-8")):
        k = x["kw"]
        if re.search(SK, k, re.I) or k in have:
            continue
        d = charter.dest_of(k)
        direct = bool(re.search(A, k))
        if not d or not (direct or (re.search(B, k) and (d != "seoul" or re.search(r"日帰り|ツアー", k)))):
            continue
        rows[k] = {"kw": k, "ko": ko(k), "kind": "대절 직접" if direct else "당일치기·투어(대절 대상)", "src": "구글 자동완성(실제)", "n": x["n"], "best": x["best"] + 1}
    for r in openpyxl.load_workbook(os.path.join(ROOT, "keywords", "구마트래블_키워드_전체.xlsx"), read_only=True).active.iter_rows(min_row=2, values_only=True):
        if re.search(A, r[1] or "") and r[1] not in rows and r[1] not in have and r[4] != "정보형" and charter.dest_of(r[1]):
            rows[r[1]] = {"kw": r[1], "ko": r[2], "kind": "대절 직접", "src": "기존 키워드(조합)", "n": r[7] or 0, "best": r[8] or ""}
    L = sorted(rows.values(), key=lambda r: (r["src"] != "구글 자동완성(실제)", r["kind"] != "대절 직접", -r["n"]))
    json.dump(L, open(KWJ, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    pl = json.load(open(PLJ, encoding="utf-8")) if os.path.exists(PLJ) else {}
    for i, x in charter.D.items():
        if i not in pl:
            km, mn = route((x["lat"], x["lng"]))
            pl[i] = {"km": km, "min": mn}
            print(i, km, mn)
            time.sleep(1)  # 공개 서버 예의
    json.dump(pl, open(PLJ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    charter = importlib.reload(charter)

    U, hd = "https://kumatravelk.com", PatternFill("solid", fgColor="3A2E2A")
    od = lambda w: (charter.LAUNCH + charter.timedelta(days=charter.WAVE_DAY[w])).isoformat()
    url = {k["kw"]: (U + "/q/" + k["slug"], od(k["wave"])) for k in charter.KW}
    for s, to in charter.KW_ALIAS.items():
        url.setdefault(s.replace("-", " "), (U + to + " (301 합침)", ""))
    wb = openpyxl.Workbook()
    s0 = wb.active
    s0.title = "지역별 요약"
    ws = wb.create_sheet("대절 키워드")
    ws.append(["No", "일본어 키워드", "한국어 뜻", "상위 지역 페이지", "구분", "출처", "자동완성 등장 수", "최고 순위", "페이지 URL", "오픈일"])
    for n, r in enumerate(L, 1):
        d = charter.dest_of(r["kw"])
        u = url.get(r["kw"], ("", ""))
        ws.append([n, r["kw"], r["ko"], U + charter.path(d), r["kind"], r["src"], r["n"], r["best"], u[0] or "같은 키워드 페이지 있음", u[1]])
    s2 = wb.create_sheet("지역 가이드 페이지")
    s2.append(["No", "지역", "페이지 URL", "서울시청에서 km", "차로 분(막힘 없음)", "키워드 페이지 수", "오픈일"])
    for n, p in enumerate(charter.PAGES, 1):
        i = p["id"]
        s2.append([n, charter.D[i]["n"], U + charter.path(i), pl[i]["km"], pl[i]["min"], len(charter.KIDS.get(i, [])), od(p["wave"])])
    s2.append([len(charter.PAGES) + 1, "ソウル市内 (기존 랜딩)", U + "/seoul-charter", "", "", len(charter.KIDS.get("seoul", [])), "공개 중"])
    s2.append([len(charter.PAGES) + 2, "허브", U + "/charter", "", "", "", "공개 중"])
    s0.append(["상위 페이지", "키워드 수", "실제 자동완성", "키워드 페이지"])
    for i in list(charter.D) + ["seoul"]:
        g = [r for r in L if charter.dest_of(r["kw"]) == i]
        s0.append([charter.label(i), len(g), sum(r["src"].startswith("구글") for r in g), len(charter.KIDS.get(i, []))])
    s0.append(["합계", len(L), sum(r["src"].startswith("구글") for r in L), len(charter.KW)])
    s0.append([])
    s0.append(["새 페이지 합계", f"지역 가이드 {len(charter.PAGES)} + 허브 1 + 키워드 페이지 {len(charter.KW)} = {len(charter.PAGES) + 1 + len(charter.KW)}"])
    s0.append(["오픈", f"CHARTER_LAUNCH={charter.LAUNCH}(금) 묶음 1 → 토 묶음 2 → 일 묶음 3·4"])
    s0.append(["요금", "서울 시내 반나절 300,000원·하루 500,000원, 서울 밖은 견적 (사이트 확정 사실만 사용)"])
    for w, (sh, widths) in enumerate([(s0, [34, 12, 14, 14]), (ws, [6, 40, 34, 40, 22, 18, 10, 8, 60, 12]), (s2, [6, 30, 48, 14, 16, 14, 12])]):
        for c in sh[1]:
            c.font, c.fill, c.alignment = Font(bold=True, color="FFFFFF"), hd, Alignment(horizontal="center")
        for j, x in enumerate(widths):
            sh.column_dimensions[chr(65 + j)].width = x
        sh.freeze_panes = "A2"
    wb.save(XLSX)
    sys.stdout.reconfigure(encoding="utf-8")
    print("keywords", len(L), "pages", len(charter.PAGES), "kw pages", len(charter.KW), "merged", len(charter.KW_ALIAS))


if __name__ == "__main__":
    main()
