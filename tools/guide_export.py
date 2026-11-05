"""가이드 86페이지 일본어 본문 → seo/guide_src_ja.json (번역 원문). 번역본은 seo/guide_tr/{ko,en}_*.json.
usage: python tools/guide_export.py [묶음 수]   — 묶음별 파일 seo/guide_tr/src_N.json 도 만든다
"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import guide

out = {p["id"]: guide.src(p) for p in guide.PAGES}
json.dump(out, open(os.path.join(guide.BASE, "seo", "guide_src_ja.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n = int(sys.argv[1]) if len(sys.argv) > 1 else 0
ids = list(out)
for i in range(n):
    part = {k: out[k] for k in ids[i::n]}
    json.dump(part, open(os.path.join(guide.BASE, "seo", "guide_tr", f"src_{i + 1}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "pages")
