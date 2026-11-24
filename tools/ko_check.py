"""한국어 페이지 형식 점검 (빌드 없이 Flask 테스트 클라이언트로 전 페이지 렌더).

h1 = 키워드 + 수식어, title 앞 == h1, 40자 이하, og:title == title, description 45~80자,
title·description·h1 중복 0, 키워드 든 h2 4개 이상, FAQPage, 사이트맵 lastmod.
    python tools/ko_check.py
"""
import html, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import app as A, guide

c = A.app.test_client()
tag = lambda s: html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
meta = lambda h, k: html.unescape(re.search(rf'<meta (?:name|property)="{k}" content="([^"]*)"', h).group(1))
pages = [p for p in guide.open_pages() if p["id"] in guide.TR["ko"]]
seen, bad, kwh2 = {"t": set(), "d": set(), "h": set()}, [], []
for path in ["/ko/guide"] + [f"/ko/{p['id']}" for p in pages]:
    r = c.get(path)
    assert r.status_code == 200, path
    h = r.get_data(as_text=True)
    title = html.unescape(re.search(r"<title>(.*?)</title>", h).group(1))
    m = re.search(r'<h1><span>(.*?)</span> <span class="hero-sub">(.*?)</span></h1>', h)
    if not m:
        bad.append((path, "h1 수식어 없음"))
        continue
    kw, sub = tag(m.group(1)), tag(m.group(2))
    h1, desc = f"{kw} {sub}", meta(h, "description")
    e = []
    if not (title == h1 or title == f"{h1} | {guide.BRAND_KO}"):
        e.append(f"title 앞≠h1: {title}")
    if len(title) > 40:
        e.append(f"title {len(title)}자")
    if meta(h, "og:title") != title or meta(h, "twitter:title") != title:
        e.append("og/twitter:title≠title")
    if meta(h, "og:site_name") != guide.BRAND_KO:
        e.append("og:site_name")
    if not 45 <= len(desc) <= 80 or not (desc.startswith(kw) or path == "/ko/guide"):
        e.append(f"description {len(desc)}자: {desc}")
    if any(w[:2] in kw for w in re.findall(r"[가-힣]{2,}", sub)) and path != "/ko/guide":
        e.append(f"수식어가 키워드 낱말 반복: {sub}")
    for k, v in (("t", title), ("d", desc), ("h", h1)):
        if v in seen[k]:
            e.append(f"중복 {k}: {v}")
        seen[k].add(v)
    if path != "/ko/guide":
        h2 = [tag(x) for x in re.findall(r"<h2[^>]*>(.*?)</h2>", h, re.S)]
        n = sum(kw in x for x in h2)
        kwh2.append((n, len(h2)))
        if n < 4:
            e.append(f"키워드 h2 {n}/{len(h2)}")
        if '"FAQPage"' not in h or h.count('href="/') < 10:
            e.append("FAQPage·내부링크")
        if re.search(r"[\U0001F300-\U0001FAFF]", "".join(h2)):
            e.append("h2 이모지")
    if e:
        bad.append((path, e))
sm = c.get("/sitemap.xml").get_data(as_text=True)
ko = re.findall(r"<loc>[^<]*/ko/[^<]*</loc><lastmod>([^<]+)", sm)
ja = set(re.findall(r"<loc>[^<]*/q/[^<]*</loc><lastmod>([^<]+)", sm))
for p in ("/guide", "/en/guide", f"/{pages[0]['id']}", f"/en/{pages[0]['id']}"):  # 다른 언어는 그대로(수식어 span 없음)
    assert "hero-sub" not in c.get(p).get_data(as_text=True), p
print("한국어 가이드", len(pages), "+ 허브 1 | 사이트맵 /ko/ lastmod", sorted(set(ko)), len(ko), "쪽 | /q/ lastmod", ja)
print("키워드 h2 최소", min(kwh2), "| 평균", round(sum(a for a, _ in kwh2) / len(kwh2), 1), "/", round(sum(b for _, b in kwh2) / len(kwh2), 1))
print("title 길이", min(map(len, seen["t"])), "~", max(map(len, seen["t"])), "| 상호 붙은 title", sum(t.endswith(guide.BRAND_KO) for t in seen["t"]),
      "| description 길이", min(map(len, seen["d"])), "~", max(map(len, seen["d"])))
for b in bad:
    print("미달", b)
assert not bad and set(ko) == {guide.UPDATED["ko"]}
print("ok")
