"""서로 다른 페이지 주소가 정확히 2,000개가 되도록, 아직 안 쓴 키워드를 점수순으로 골라 seo/kw_extra.json 에 넣는다.

  python -I tools/add_keywords.py   (그다음 python tools/build_url_xlsx.py)
같은 키워드(단어 순서·国際空港·から 차이)는 guide.kw_norm 으로 걸러 1페이지만 만든다.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import select_pages as sp
from openpyxl import load_workbook

OUT = os.path.join(sp.ROOT, "seo", "kw_extra.json")
json.dump([], open(OUT, "w"))  # 기존 추가분 없이 다시 계산
import guide

TOTAL = 2000
landing = 4  # 메인·seoul-sougei·seoul-charter·incheon-airport-sougei
need = TOTAL - len(guide.PAGES) - landing - len(guide.KW)
used = {guide.kw_norm(k["kw"]) for k in guide.KW} | {guide.kw_norm(p["main"]) for p in guide.PAGES} | {guide.kw_norm(k) for p in guide.PAGES for k in p["kws"]}
W_SRC, W_PRI = {"실제 검색어": 300, "패턴 조합": 100, "서비스 조합": 80}, {1: 200, 2: 100, 3: 0}
cand = []
for r in list(load_workbook(sp.SRC, read_only=True).active.iter_rows(values_only=True))[1:]:
    _, ja, ko, src, kind, ap, pop, hits, best, pri, use = r[:11]
    if kind in ("정보형", "대중교통 비교"):
        continue
    pid = sp.page_of(ja, kind, use or "")[0]
    pid = guide.MERGED.get(pid, pid)
    n = guide.kw_norm(ja)
    if pid in guide.BY_ID and n not in used:
        used.add(n)
        cand.append((-(W_SRC[src] + W_PRI[pri] + (hits or 0) * 20 + ((10 - best) if best else 0)), len(cand), ja, pid))
pick = sorted(cand)[:need]
json.dump([{"kw": ja, "parent": pid} for _, _, ja, pid in pick], open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
sys.stdout.reconfigure(encoding="utf-8")
print("added", len(pick), "of", len(cand))
