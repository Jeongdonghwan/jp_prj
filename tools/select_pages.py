"""구마트래블_키워드_전체.xlsx → 우선순위 2,000개 선정 + 같은 의도끼리 페이지로 묶기.

  python -I tools/select_pages.py
  → keywords/구마트래블_제작_2000.xlsx (시트1 키워드 2,000 · 시트2 페이지 목록)
  → seo/pages.json (빌드 입력)

페이지 = (공항, 장소, 방향, 의도). "明洞/ミョンドン", "料金/いくら/値段" 같은 표기·어휘 변형은 한 페이지의 보조 키워드가 된다.
"""
import json, os, re, sys
from collections import Counter, defaultdict
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "keywords", "구마트래블_키워드_전체.xlsx")
OUT = os.path.join(ROOT, "keywords", "구마트래블_제작_2000.xlsx")
PAGES = os.path.join(ROOT, "seo", "pages.json")
N = 2000

AIRPORTS = [("icn", "仁川空港", "인천공항", r"仁川|インチョン"), ("gmp", "金浦空港", "김포공항", r"金浦|キンポ")]

# (slug, 일본어, 한국어, 별칭 정규식) — 앞쪽이 더 구체적. 호텔명 안의 지명도 잡힌다.
PLACES = [
    ("myeongdong", "明洞", "명동", r"明洞|ミョンドン"),
    ("hongdae", "弘大", "홍대", r"弘大|ホンデ|延南洞|合井|新村"),
    ("gangnam", "江南", "강남", r"江南|カンナム|ノンヒョン|論峴|シンノンヒョン|駅三|教大|新沙|カロスキル|狎鴎亭|清潭"),
    ("dongdaemun", "東大門", "동대문", r"東大門|トンデムン|ddp|DDP"),
    ("namdaemun", "南大門", "남대문", r"南大門|会賢"),
    ("jongno", "鍾路・仁寺洞", "종로·인사동", r"鍾路|仁寺洞|益善洞|北村|景福宮|光化門|市庁|カンジャンシジャン|広蔵市場"),
    ("euljiro", "乙支路", "을지로", r"乙支路|忠武路"),
    ("itaewon", "梨泰院", "이태원", r"梨泰院|イテウォン"),
    ("yongsan", "龍山", "용산", r"龍山|ヨンサン"),
    ("seongsu", "聖水", "성수", r"聖水|ソンス"),
    ("jamsil", "蚕室", "잠실", r"蚕室|チャムシル|ロッテワールド|lotte world"),
    ("samseong", "三成・COEX", "삼성·코엑스", r"三成|サムソン|coex|COEX|宣陵|ソンルン"),
    ("yeouido", "汝矣島", "여의도", r"汝矣島|麻浦|孔徳"),
    ("yeongdeungpo", "永登浦", "영등포", r"永登浦|九老|デジタル団地"),
    ("seoul-station", "ソウル駅", "서울역", r"ソウル駅"),
    ("walkerhill", "ウォーカーヒル", "워커힐", r"ウォーカーヒル"),
    ("songdo", "松島", "송도", r"松島"),
    ("incheon-city", "仁川市内", "인천 시내", r"仁川駅|チャイナタウン|月尾島|富平"),
    ("paradise-city", "パラダイスシティ", "파라다이스시티", r"パラダイスシティ"),
    ("unseo", "雲西", "운서", r"雲西|ウンソ"),
    ("magok", "麻谷", "마곡", r"マゴク|鉢山|発山"),
    ("seoul", "ソウル", "서울", r"ソウル|市内"),
]
TRIPS = [("nami-island", r"南怡島"), ("gapyeong", r"加平|プチフランス"), ("dmz", r"DMZ|板門店|坡州"),
         ("suwon", r"水原"), ("ganghwa", r"江華島"), ("chuncheon", r"春川"), ("icheon", r"利川|驪州"),
         ("folk-village", r"韓国民俗村"), ("everland", r"エバーランド"), ("pyeongchang", r"平昌"), ("sokcho", r"束草|江陵"),
         ("yangpyeong", r"楊平"), ("pocheon", r"抱川"), ("gwangmyeong", r"光明洞窟")]
PURPOSES = [("golf", r"ゴルフ"), ("kpop", r"コンサート|K-POP|推し活"), ("business", r"出張|ビジネス"), ("wedding", r"結婚式"),
            ("beauty", r"美容皮膚科|美容整形|病院"), ("shopping", r"免税店|ショッピング"), ("casino", r"カジノ"),
            ("group-trip", r"卒業旅行|社員旅行|修学旅行"), ("senior", r"シニア")]
VEHICLES = [("staria", r"スターリア"), ("solati", r"ソラティ|15人乗り"), ("genesis", r"ジェネシス|高級車|リムジン"),
            ("van", r"ワゴン車|ミニバン|大型車")]

INTENTS = [  # 위에서부터 먼저 걸리는 것
    ("nimotsu", "荷物配送", r"荷物|スーツケース|キャリー|配送|手ぶら"),
    ("kotsu", "バス・電車比較", r"リムジンバス|バス|電車|arex|a.?rex|エーレックス|地下鉄|空港鉄道|鉄道|列車|時刻表|直通|特急|快速|始発|終電|モノレール"),
    ("taxi", "タクシー", r"タクシー|uber|ウーバー|カカオ|配車|模範"),
    ("sougei", "送迎", r"送迎|ハイヤー|チャーター|貸切|専用車|リムジン|ジャンボ|大型|レンタカー|ピックアップ"),
    ("ikikata", "行き方", r"."),
]
EXISTING = {"/seoul-sougei": "seoul-sougei", "/seoul-charter": "seoul-charter", "/incheon-airport-sougei": "incheon-airport-sougei", "/": "home"}


def first(table, kw, idx=-1):
    for t in table:
        if re.search(t[idx], kw):
            return t
    return None


def page_of(kw, kind, use):
    """→ (page_id, 유형, 공항, 장소 slug, 방향, 의도)"""
    if kind == "정보형":
        return "blog", "블로그 글", "", "", "", ""
    ap = first(AIRPORTS, kw)
    if ap:
        intent = first(INTENTS, kw)[0]
        if re.search(AIRPORTS[0][3], kw) and re.search(AIRPORTS[1][3], kw):
            return "icn-gmp-transfer", "공항 경로", "icn+gmp", "", "공항↔공항", intent
        pl = first(PLACES, kw)
        place = pl[0] if pl else ""
        # "明洞から仁川空港", "東大門 から 金浦空港" → 시내에서 공항(출국): 지명 < から < 공항 순서
        m_pl, m_ap, m_kara = re.search(pl[3], kw) if pl else None, re.search(ap[3], kw), kw.find("から")
        rev = bool(m_pl) and 0 <= kw.find("から") and m_pl.start() < m_kara < m_ap.start()
        if not place and intent == "ikikata":  # 공항만 있는 일반 이동 검색은 세부 상황별로 나눈다
            for sub, rx in (("shinya", r"深夜|夜中|夜着|夜に|夜"), ("soucho", r"早朝|始発|朝"),
                            ("terminal", r"ターミナル|t1|t2|T1|T2|第1|第2|第一|第二"), ("hotel", r"ホテル")):
                if re.search(rx, kw):
                    intent = sub
                    break
        if place:  # 지역 경로는 두 갈래로: 택시·픽업(차로 가기) / 가는 법·버스·전철 비교
            intent = {"sougei": "taxi", "kotsu": "ikikata"}.get(intent, intent)
        if not place:
            pid = f"{ap[0]}-{intent}"
        elif rev:
            pid = f"{place}-to-{ap[0]}-{intent}"
        else:
            pid = f"{ap[0]}-{place}-{intent}"
        return pid, "공항 경로", ap[0], place, "출국(시내→공항)" if rev else "입국(공항→시내)", intent
    for table, prefix, label in ((TRIPS, "charter", "근교 대절"), (PURPOSES, "purpose", "목적별"), (VEHICLES, "vehicle", "차종")):
        t = first(table, kw, 1)
        if t:
            return f"{prefix}-{t[0]}", label, "", t[0], "", ""
    return EXISTING.get(use.split(" ")[0], "home"), "기존 랜딩", "", "", "", ""


def main():
    ws = load_workbook(SRC, read_only=True).active
    rows = list(ws.iter_rows(values_only=True))[1:]
    W_SRC = {"실제 검색어": 300, "패턴 조합": 100, "서비스 조합": 80}
    W_PRI = {1: 200, 2: 100, 3: 0}
    items = []
    for r in rows:
        _, ja, ko, src, kind, ap, pop, hits, best, pri, use = r[:11]
        if kind == "대중교통 비교" and (hits or 0) < 2:
            continue  # 버스·전철 시간표만 찾는 1회성 검색은 제외
        score = W_SRC[src] + W_PRI[pri] + (hits or 0) * 20 + ((10 - best) if best else 0)
        items.append({"ja": ja, "ko": ko, "src": src, "kind": kind, "pop": pop, "hits": hits or 0, "score": score, "use": use or ""})
    items.sort(key=lambda x: -x["score"])
    pick = items[:N]

    pages = defaultdict(lambda: {"kws": []})
    for x in pick:
        pid, ptype, ap, place, direction, intent = page_of(x["ja"], x["kind"], x["use"])
        if pid == "blog":
            pid = "blog:" + x["ja"]
        x["page"] = pid
        p = pages[pid]
        p.update(id=pid, type=ptype, airport=ap, place=place, direction=direction, intent=intent)
        p["kws"].append(x)
    plist = []
    for p in pages.values():
        p["score"] = sum(k["score"] for k in p["kws"])
        p["main"] = max(p["kws"], key=lambda k: k["score"])
        plist.append(p)
    plist.sort(key=lambda p: -p["score"])
    # 오픈 묶음: 페이지 점수순 4등분 (site-launch/post-launch 의 나눠 열기)
    new = [p for p in plist if p["type"] not in ("기존 랜딩", "블로그 글")]
    for i, p in enumerate(new):
        p["wave"] = 1 + i * 4 // len(new)
    for p in plist:
        p.setdefault("wave", 0 if p["type"] == "기존 랜딩" else "")
        main = p["main"]
        p["main"]["is_main"] = True

    HEAD = PatternFill("solid", fgColor="FF6F91")
    wb = Workbook()

    def sheet(ws, header, data, widths):
        ws.append(header)
        for c in ws[1]:
            c.font, c.fill, c.alignment = Font(bold=True, color="FFFFFF"), HEAD, Alignment(horizontal="center")
        for d in data:
            ws.append(d)
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
        ws.freeze_panes = "B2"
        ws.auto_filter.ref = ws.dimensions

    url = lambda pid: "블로그 글 후보" if pid.startswith("blog:") else ("/" if pid == "home" else f"/{pid}")
    ws = wb.active
    ws.title = "키워드 2000"
    sheet(ws, ["No", "일본어 키워드", "한국어 키워드", "출처", "분류", "인기도", "점수", "페이지 URL", "대표 키워드", "오픈 묶음"],
          [[i + 1, x["ja"], x["ko"], x["src"], x["kind"], x["pop"], x["score"], url(x["page"]),
            "대표" if x.get("is_main") else "", pages[x["page"]]["wave"]] for i, x in enumerate(pick)],
          [7, 42, 40, 11, 14, 8, 7, 40, 8, 9])
    sheet(wb.create_sheet("페이지 목록"),
          ["No", "페이지 URL", "대표 일본어 키워드", "대표 한국어 키워드", "유형", "공항", "장소", "방향", "의도", "키워드 수", "페이지 점수", "오픈 묶음", "보조 키워드(일부)"],
          [[i + 1, url(p["id"]), p["main"]["ja"], p["main"]["ko"], p["type"], p["airport"], p["place"], p["direction"], p["intent"],
            len(p["kws"]), p["score"], p["wave"], " / ".join(k["ja"] for k in p["kws"] if k is not p["main"])[:300]]
           for i, p in enumerate(plist)],
          [6, 36, 40, 36, 10, 6, 14, 14, 9, 8, 9, 8, 80])
    wb.save(OUT)
    json.dump([{k: v for k, v in p.items() if k != "main"} | {"main": p["main"]["ja"], "kws": [k["ja"] for k in p["kws"]]}
               for p in plist if not p["id"].startswith("blog:")], open(PAGES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    sys.stdout.reconfigure(encoding="utf-8")
    print("picked", len(pick), Counter(x["src"] for x in pick), Counter(x["kind"] for x in pick))
    print("pages", len(plist), Counter(p["type"] for p in plist))
    print("new pages by intent", Counter(p["intent"] for p in new), "waves", Counter(p["wave"] for p in new))
    print("kw per new page", Counter(min(len(p["kws"]), 10) for p in new))
    print("cutoff score", pick[-1]["score"])
    print(OUT)


if __name__ == "__main__":
    main()
