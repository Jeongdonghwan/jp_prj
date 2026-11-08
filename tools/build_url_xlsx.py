"""만든 페이지 URL 전체 → keywords/구마트래블_페이지URL_2000.xlsx (번역 다시 하거나 문구 바꾼 뒤 재실행)."""
import sys, os
from collections import Counter
from datetime import timedelta
from urllib.parse import quote, unquote
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import guide

U = "https://kumatravelk.com"
KW = os.path.join(guide.BASE, "keywords")
old = openpyxl.load_workbook(os.path.join(KW, "구마트래블_제작_2000.xlsx"))["키워드 2000"]
ko = {r[1]: r[2] for r in old.iter_rows(min_row=2, values_only=True)}
landing = {r[1]: r[7] for r in old.iter_rows(min_row=2, values_only=True)
           if r[7].strip("/") not in guide.BY_ID and r[7].strip("/") not in guide.MERGED}
od = lambda w: (guide.LAUNCH + timedelta(days=guide.WAVE_DAY[w])).isoformat()
hd = PatternFill("solid", fgColor="3A2E2A")


def sheet(wb, name, head, widths):
    ws = wb.create_sheet(name)
    ws.append(head)
    for c in ws[1]:
        c.font, c.fill, c.alignment = Font(bold=True, color="FFFFFF"), hd, Alignment(horizontal="center")
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(65 + i)].width = w
    ws.freeze_panes = "A2"
    return ws


def link(ws, col):
    c = ws.cell(ws.max_row, col)
    c.hyperlink, c.font = c.value, Font(color="0563C1", underline="single")


# 1행 = 서로 다른 페이지 1개. 같은 키워드(어순·표기만 다름)는 그 페이지의 "합친 키워드"에 넣고 옛 주소는 301
alias = {}
for slug, to in guide.KW_ALIAS.items():
    alias.setdefault(to, []).append(slug.replace("-", " "))
rows = []
for p in guide.PAGES:
    rows.append((p["main"], "가이드(대표)", f"/{p['id']}", f"/{p['id']}", guide.compose(p)["title"], p["wave"]))
    for k in guide.KIDS.get(p["id"], []):
        rows.append((k["kw"], "키워드 페이지", f"/q/{quote(k['slug'])}", f"/{p['id']}", guide.compose_kw(k)["title"], k["wave"]))
for u in dict.fromkeys(landing.values()):
    kws = [k for k, v in landing.items() if v == u]
    rows.append((kws[0], "기존 랜딩", u, u, "", None))
    alias[u] = kws[1:]
assert len(rows) == 2000 and len({r[2] for r in rows}) == 2000, len(rows)
merged = lambda path: " / ".join(alias.get(unquote(path), []))

wb = openpyxl.Workbook()
s0 = wb.active
s0.title = "요약"
s0.column_dimensions["A"].width, s0.column_dimensions["B"].width = 30, 72
ws = sheet(wb, "페이지 URL 2000", ["No", "일본어 키워드", "한국어 키워드", "페이지 종류", "페이지 URL", "상위 가이드 페이지", "페이지 제목", "오픈 묶음", "오픈일", "같은 페이지로 합친 키워드"],
           [6, 38, 32, 13, 70, 48, 60, 9, 12, 60])
for i, (kw, typ, path, parent, title, w) in enumerate(rows, 1):
    ws.append([i, kw, ko.get(kw, ""), typ, U + path, U + parent, title, w or "-", od(w) if w else "공개 중", merged(path)])
    link(ws, 5)
ws.auto_filter.ref = ws.dimensions
s2 = sheet(wb, "가이드 86 (3개 언어)", ["No", "제목", "일본어 URL", "한국어 URL", "영어 URL", "하위 키워드 페이지 수", "오픈 묶음", "오픈일"],
           [6, 60, 50, 52, 52, 12, 9, 12])
for i, p in enumerate(guide.PAGES, 1):
    s2.append([i, guide.compose(p)["title"], *(U + guide.path(l, p["id"]) for l in guide.LANGS), len(guide.KIDS.get(p["id"], [])), p["wave"], od(p["wave"])])
    for col in (3, 4, 5):
        link(s2, col)
cnt, wc = Counter(r[1] for r in rows), Counter(r[5] for r in rows if r[5])
for r in [["항목", "값"], ["페이지 총수(주소 기준)", 2000], ["합친 키워드(301)", f"{len(guide.KW_ALIAS)}개 — 어순·표기만 달라 1페이지로"], *[[k, f"{v}개"] for k, v in cnt.items()],
          ["한국어·영어 가이드", f"각 {len(guide.PAGES)}개 (시트 '가이드 86')"],
          ["허브", U + "/guide"], ["키워드 목록", U + "/guide/keywords"],
          *[[f"묶음 {w} ({od(w)} 공개)", f"{wc[w]}페이지"] for w in sorted(wc)],
          ["오픈일 기준", f"PAGES_LAUNCH={guide.LAUNCH} 기준. 서버 설정이 다르면 그만큼 밀림"], ["공개 전", "404, 사이트맵·링크에서 빠짐"]]:
    s0.append(r)
for c in s0[1]:
    c.font, c.fill = Font(bold=True, color="FFFFFF"), hd
wb.save(os.path.join(KW, "구마트래블_페이지URL_2000.xlsx"))
print(dict(cnt), sorted(wc.items()))
