"""사이트 전체 페이지(공항 가이드·키워드·대절·한국어/영어판) → keywords/구마트래블_전체페이지_키워드.xlsx

  python -I tools/build_all_xlsx.py
키워드마다 구글 일본 검색 링크(hl=ja, gl=jp)를 붙인다 — 눌러서 노출 여부를 직접 확인하는 용도.
"""
import json, os, sys
from collections import Counter
from datetime import timedelta
from urllib.parse import quote
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import guide, charter

U = "https://kumatravelk.com"
KWD = os.path.join(guide.BASE, "keywords")
src = openpyxl.load_workbook(os.path.join(KWD, "구마트래블_제작_2000.xlsx"))["키워드 2000"]
ko = {r[1]: r[2] for r in src.iter_rows(min_row=2, values_only=True)}
landing = {}
for r in src.iter_rows(min_row=2, values_only=True):
    if r[7].strip("/") not in guide.BY_ID and r[7].strip("/") not in guide.MERGED:
        landing.setdefault(r[7], []).append(r[1])
ko.update({x["kw"]: x["ko"] for x in json.load(open(os.path.join(guide.BASE, "seo", "charter_kw.json"), encoding="utf-8"))})
god = lambda w: (guide.LAUNCH + timedelta(days=guide.WAVE_DAY[w])).isoformat()
cod = lambda w: (charter.LAUNCH + timedelta(days=charter.WAVE_DAY[w])).isoformat()
gq = lambda kw: "https://www.google.co.jp/search?hl=ja&gl=jp&q=" + quote(kw)

rows = []  # (분야, 종류, 일본어 키워드, 한국어, 경로, 상위 경로, 제목, 공개일)
for p in guide.PAGES:
    rows.append(("공항 이동", "가이드(대표)", p["main"], ko.get(p["main"], ""), f"/{p['id']}", "/guide", guide.compose(p)["title"], god(p["wave"])))
    for k in guide.KIDS.get(p["id"], []):
        rows.append(("공항 이동", "키워드 페이지", k["kw"], ko.get(k["kw"], ""), f"/q/{k['slug']}", f"/{p['id']}", guide.compose_kw(k)["title"], god(k["wave"])))
for u, kws in landing.items():
    rows.append(("메인·랜딩", "기존 랜딩", kws[0], ko.get(kws[0], ""), u, "/", " / ".join(kws[1:])[:120], "공개 중"))
rows.append(("메인·랜딩", "한국어 메인", "", "", "/ko", "/", "구마트래블 한국어 메인", "공개 중"))
rows.append(("공항 이동", "허브", "仁川空港 金浦空港 アクセス", "인천공항 김포공항 가는 법", "/guide", "/", guide.UI["ja"]["hub_t"], "공개 중"))
rows.append(("공항 이동", "키워드 목록", "", "", "/guide/keywords", "/guide", "よく調べられている質問 一覧", "공개 중"))
rows.append(("대절", "허브", "韓国 貸切チャーター", "한국 대절", "/charter", "/", "韓国 貸切チャーターガイド", "공개 중"))
for p in charter.PAGES:
    g = charter.compose(p["id"])
    kw = f"ソウルから{charter.D[p['id']]['n']} 貸切"
    rows.append(("대절", "지역 가이드", kw, "", charter.path(p["id"]), "/charter", g["title"], cod(p["wave"])))
for k in charter.KW:
    rows.append(("대절", "키워드 페이지", k["kw"], ko.get(k["kw"], ""), f"/q/{k['slug']}", charter.path(k["parent"]), charter.compose_kw(k)["title"], cod(k["wave"])))
for lang in ("ko", "en"):
    rows.append((f"{lang} 번역", "허브", "", "", f"/{lang}/guide", "/guide", guide.UI[lang]["hub_t"], "공개 중"))
    for p in guide.PAGES:
        if p["id"] in guide.TR[lang]:
            rows.append((f"{lang} 번역", "가이드 번역", guide.TR[lang][p["id"]]["title"].split("｜")[0], "", guide.path(lang, p["id"]), f"/{p['id']}", guide.TR[lang][p["id"]]["title"], god(p["wave"])))
assert len({r[4] for r in rows}) == len(rows), "주소 중복"

hd = PatternFill("solid", fgColor="3A2E2A")
wb = openpyxl.Workbook()
s0 = wb.active
s0.title = "요약"
ws = wb.create_sheet("전체 페이지")
ws.append(["No", "분야", "페이지 종류", "일본어 키워드", "한국어 뜻", "페이지 URL", "상위 페이지", "페이지 제목", "공개일", "구글 일본 검색"])
for i, r in enumerate(rows, 1):
    ws.append([i, *r[:4], U + r[4], U + r[5], r[6], r[7], "검색해 보기" if r[2] else ""])
    for col, link in ((6, U + r[4]), (10, gq(r[2]) if r[2] else None)):
        if link:
            c = ws.cell(ws.max_row, col)
            c.hyperlink, c.font = link, Font(color="0563C1", underline="single")
ws.auto_filter.ref = ws.dimensions
cnt = Counter((r[0], r[1]) for r in rows)
s0.append(["분야", "페이지 종류", "페이지 수"])
for (a, b), n in cnt.items():
    s0.append([a, b, n])
s0.append(["합계", "", len(rows)])
s0.append([])
s0.append(["확인 방법", "'전체 페이지' 시트의 '검색해 보기'를 누르면 구글 일본(google.co.jp) 검색 결과가 열립니다. 로그인·검색 기록에 따라 순위가 조금 다르게 보일 수 있습니다."])
s0.append(["정확한 노출 수치", "구글 서치콘솔 > 실적(검색어별 노출·클릭·평균 순위), 페이지 > 색인 생성됨"])
for sh, widths in ((s0, [16, 16, 10]), (ws, [6, 10, 13, 40, 34, 60, 46, 60, 12, 12])):
    for c in sh[1]:
        c.font, c.fill, c.alignment = Font(bold=True, color="FFFFFF"), hd, Alignment(horizontal="center")
    for j, w in enumerate(widths):
        sh.column_dimensions[chr(65 + j)].width = w
    sh.freeze_panes = "A2"
out = os.path.join(KWD, "구마트래블_전체페이지_키워드.xlsx")
wb.save(out)
sys.stdout.reconfigure(encoding="utf-8")
print(len(rows), dict(cnt))
