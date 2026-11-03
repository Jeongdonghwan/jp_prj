"""일본 구글 자동완성(hl=ja, gl=jp)으로 인천·김포공항 관련 실제 검색어를 모은다.
자동완성에 뜬다 = 일본에서 실제로 자주 검색된다. 뜬 횟수·순위로 인기 점수를 매긴다.

  python -I tools/airport_suggest.py   → keywords/airport_suggest_raw.json
"""
import json, os, sys, time, urllib.parse, urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "keywords", "airport_suggest_raw.json")

SEEDS = ["仁川空港", "金浦空港", "インチョン空港", "キンポ空港", "仁川国際空港", "金浦国際空港",
         "仁川空港から", "金浦空港から", "仁川空港 ソウル", "金浦空港 ソウル", "仁川空港 送迎", "金浦空港 送迎",
         "仁川空港 タクシー", "金浦空港 タクシー", "仁川空港 移動", "金浦空港 移動", "仁川空港 明洞", "金浦空港 明洞",
         "仁川空港 深夜", "仁川空港 荷物", "ソウル 空港送迎", "韓国 空港送迎", "仁川空港 ホテル", "金浦空港 ホテル",
         "ソウルから仁川空港", "明洞から仁川空港", "ソウルから金浦空港", "仁川空港 行き方", "金浦空港 行き方",
         "仁川空港 第2ターミナル", "仁川空港 早朝", "仁川空港 弘大", "仁川空港 江南", "仁川空港 東大門"]
KANA = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわん"
SUFFIX = [" "] + [" " + c for c in KANA] + [" " + c for c in "abcdefghijklmnopqrstuvwxyz"]


def suggest(q):
    u = "https://suggestqueries.google.com/complete/search?client=firefox&hl=ja&gl=jp&q=" + urllib.parse.quote(q)
    for _ in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=10)
            return q, json.loads(r.read().decode("utf-8"))[1]
        except Exception:
            time.sleep(2)
    return q, []


def main():
    qs = [s + x for s in SEEDS for x in SUFFIX]
    hits = defaultdict(lambda: {"n": 0, "best": 99, "seed": ""})
    with ThreadPoolExecutor(4) as ex:
        for q, res in ex.map(suggest, qs):
            for rank, k in enumerate(res):
                k = " ".join(k.split())
                h = hits[k]
                h["n"] += 1
                h["best"] = min(h["best"], rank)
                h["seed"] = h["seed"] or q.strip()
    # 점수: 여러 질의에서 반복 등장 + 순위가 높을수록 인기
    rows = [{"kw": k, "hits": v["n"], "best_rank": v["best"] + 1, "score": v["n"] * 10 + (10 - v["best"]), "seed": v["seed"]}
            for k, v in hits.items()]
    rows.sort(key=lambda r: -r["score"])
    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sys.stdout.reconfigure(encoding="utf-8")
    print(len(qs), "queries ->", len(rows), "keywords ->", OUT)


if __name__ == "__main__":
    main()
