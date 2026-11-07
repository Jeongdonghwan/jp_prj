"""번역본 점검: 구조(섹션·문단·표·FAQ 개수)와 숫자가 원문과 같은지, 일본어 문자가 남았는지.
usage: python tools/guide_tr_check.py ko 1   (seo/guide_tr/src_1.json ↔ ko_1.json)
"""
import sys, os, json, re
sys.stdout.reconfigure(encoding="utf-8")
lang, n = sys.argv[1], sys.argv[2]
D = os.path.join(os.path.dirname(__file__), "..", "seo", "guide_tr")
src = json.load(open(os.path.join(D, f"src_{n}.json"), encoding="utf-8"))
tr = json.load(open(os.path.join(D, f"{lang}_{n}.json"), encoding="utf-8"))
errs = []
ban = re.compile({"ko": r"택시|전철|지하철|리무진|공항철도", "en": r"(?i)(taxis?|cabs?|trains?|subway|metro|limousine|AREX)"}[lang])  # 다른 교통수단 언급 금지
MON = {m: str(i + 1) for i, m in enumerate("January February March April May June July August September October November December".split())}


def nums(s):
    x = json.dumps(s, ensure_ascii=False).replace(",", "")
    x = re.sub(r"\b(" + "|".join(MON) + r")\b", lambda m: MON[m.group(1)], x)  # November 2026 → 11 2026
    x = re.sub(r"(\d):00\b", r"\1", x)  # 9:00 → 9
    return sorted(n for n in re.findall(r"\d+(?:[.]\d+)*", x) if n not in ("00", "1"))  # 23時00分 ↔ 23:00 ↔ 23시
kana = re.compile(r"[぀-ヿ]")


def shape(x):
    return [shape(y) for y in x] if isinstance(x, list) else 0


for pid, s in src.items():
    t = tr.get(pid)
    if not t:
        errs.append(f"{pid}: 없음"); continue
    for k in ("title", "desc", "h1", "lead", "box", "secs", "table", "flow", "faq", "img_alt", "label"):
        if k not in t:
            errs.append(f"{pid}.{k}: 키 없음"); continue
        if shape(s[k]) != shape(t[k]):
            errs.append(f"{pid}.{k}: 구조 다름 (섹션·문단·행 개수를 원문과 같게)")
        a, b = nums(s[k]), nums(t[k])
        if k not in ("title", "desc", "h1", "label") and a != b:
            miss = [x for x in a if a.count(x) > b.count(x)][:5]
            extra = [x for x in b if b.count(x) > a.count(x)][:5]
            errs.append(f"{pid}.{k}: 숫자 다름 빠짐{miss} 추가{extra}")
        if ban.search(json.dumps(t[k], ensure_ascii=False)):
            errs.append(f"{pid}.{k}: 다른 교통수단 언급 {ban.search(json.dumps(t[k], ensure_ascii=False)).group()}")
        if kana.search(json.dumps(t[k], ensure_ascii=False)):
            errs.append(f"{pid}.{k}: 일본어 가나가 남음")
    t["_src"] = s["_src"]
json.dump(tr, open(os.path.join(D, f"{lang}_{n}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n".join(errs) if errs else f"OK {lang}_{n}: {len(src)} pages")
