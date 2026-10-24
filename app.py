import os, json, smtplib, threading, time
from datetime import datetime
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, abort, Response, url_for
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)
_lock = threading.Lock()

CFG = {
    "site_url": os.getenv("SITE_URL", "http://localhost:5000").rstrip("/"),
    "phone": os.getenv("PHONE", "010-6432-7759"),
    "email": os.getenv("EMAIL", "jk080222@naver.com"),
    # 서치콘솔/서치어드바이저 소유확인 content 값 (쉼표로 여러 개 가능)
    "google_verify": [v for v in os.getenv("GOOGLE_VERIFY", "").split(",") if v.strip()],
    "naver_verify": [v for v in os.getenv("NAVER_VERIFY", "").split(",") if v.strip()],
    "line_url": os.getenv("LINE_URL", "https://line.me/ti/p/LIBV24b97K"),
}
I18N = {
    lang: json.load(open(os.path.join(BASE, "i18n", f"{lang}.json"), encoding="utf-8"))
    for lang in ("ja", "ko")
}
PRICES = {"icn": 150000, "gmp": 80000, "half": 300000, "full": 500000, "rt_off": 0.10}

GALLERY = [(f"memory-{i:02d}", "memory", f"cap_m{i}") for i in range(1, 15)] + [  # (파일명, 카테고리, 캡션 키)
    ("gwanghwamun-snow", "scenery", "cap_gwanghwamun"),
    ("hangang-night", "scenery", "cap_hangang"),
    ("gyeongbokgung-guard", "scenery", "cap_guard"),
    ("lotte-tower-night", "scenery", "cap_lotte"),
    ("namsan-tower-winter", "scenery", "cap_namsan_winter"),
    ("namsan-moon", "scenery", "cap_namsan_moon"),
    ("bukhansan-view", "scenery", "cap_bukhansan"),
    ("seoul-night-skyline", "scenery", "cap_skyline"),
    ("namsan-sunset", "scenery", "cap_namsan_sunset"),
    ("staria-limo", "vehicle", "cap_staria"),
    ("genesis-vip", "vehicle", "cap_genesis"),
    ("solati", "vehicle", "cap_solati"),
]


def _load(name):
    p = os.path.join(DATA, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


def _append(name, row):
    with _lock:
        rows = _load(name)
        rows.append(row)
        json.dump(rows, open(os.path.join(DATA, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def _mail(subject, body):
    host = os.getenv("SMTP_HOST")
    if not host:
        return
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, os.getenv("SMTP_USER"), os.getenv("MAIL_TO")
    msg.set_content(body)
    try:
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", 587))) as s:
            s.starttls()
            s.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
            s.send_message(msg)
    except Exception as e:  # 메일 실패해도 JSON에는 저장됨
        app.logger.warning("mail failed: %s", e)


_last_post = {}


def _rate_limited(ip):  # ponytail: 프로세스 내 메모리, 워커 1개 기준. 스팸 심하면 캡차로.
    now = time.time()
    if now - _last_post.get(ip, 0) < 60:
        return True
    _last_post[ip] = now
    return False


def _ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()


def _lastmod(lang):
    """본문을 만드는 파일의 최신 수정시각 (레이아웃 외 날짜 위조 없음)."""
    files = [os.path.join(BASE, "templates", "index.html"), os.path.join(BASE, "i18n", f"{lang}.json")]
    return datetime.fromtimestamp(max(os.path.getmtime(f) for f in files))


def _jsonld(t, reviews, avg, lp=None, path="/"):
    u = CFG["site_url"]
    biz = {
        "@type": "LocalBusiness", "@id": u + "/#business", "name": t["brand"] + " / Kuma Travel", "url": u,
        "telephone": "+82-" + CFG["phone"][1:], "email": CFG["email"], "image": u + "/static/img/og.jpg", "description": t["meta_desc"],
        "priceRange": "₩80,000 - ₩500,000", "areaServed": ["Seoul", "Incheon", "Gimpo"],
        "address": {"@type": "PostalAddress", "addressLocality": "Seoul", "addressCountry": "KR"},
        "openingHours": "Mo-Su 00:00-24:00",
        "makesOffer": [{"@type": "Offer", "name": t[k], "price": PRICES[p], "priceCurrency": "KRW"}
                       for k, p in (("price_icn", "icn"), ("price_gmp", "gmp"), ("price_half", "half"), ("price_full", "full"))],
    }
    if reviews:
        biz["aggregateRating"] = {"@type": "AggregateRating", "ratingValue": avg, "reviewCount": len(reviews)}
        biz["review"] = [{"@type": "Review", "author": {"@type": "Person", "name": r["name"]}, "datePublished": r["at"],
                          "reviewBody": r["body"], "reviewRating": {"@type": "Rating", "ratingValue": r["rating"]}}
                         for r in reviews[:10]]
    faq = {"@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in t["faq"]]}
    site = {"@type": "WebSite", "@id": u + "/#website", "name": t["brand"], "alternateName": "Kuma Travel",
            "url": u + "/", "inLanguage": ["ja", "ko"], "publisher": {"@id": u + "/#business"}}
    graph = [site, biz, faq]
    if lp:
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": t["brand"], "item": u + "/"},
            {"@type": "ListItem", "position": 2, "name": lp["kw"], "item": u + path}]})
    return {"@context": "https://schema.org", "@graph": graph}


LANDINGS = I18N["ja"]["landings"]  # 일본어 키워드 전용 페이지 (slug → 문구)


def render(lang, slug=None):
    t, lp = I18N[lang], None
    if slug:  # 랜딩: 메인 문구 위에 키워드 문구만 덮어쓴다
        lp = LANDINGS[slug]
        t = {**t, "meta_title": lp["meta_title"], "meta_desc": lp["meta_desc"], "hero_h1": lp["h1"],
             "hero_sub": lp["lead"], "hero_eyebrow": lp["kw"] + "｜" + t["brand"],
             "intro_title": lp["intro_title"], "intro": lp["intro"], "faq": lp["faq"] + t["faq"]}
    path = f"/{slug}" if slug else ("/ko" if lang == "ko" else "/")
    reviews = [r for r in _load("reviews.json") if r.get("approved")][::-1]
    avg = round(sum(r["rating"] for r in reviews) / len(reviews), 1) if reviews else 0
    return render_template(
        "index.html", t=t, lang=lang, cfg=CFG, prices=PRICES, gallery=GALLERY, ld=_jsonld(t, reviews, avg, lp, path),
        reviews=reviews, avg=avg, sent=request.args.get("sent"), year=datetime.now().year,
        lp=lp, path=path, landings=LANDINGS,
    )


@app.route("/<slug>")
def landing(slug):
    if slug not in LANDINGS:
        abort(404)
    return render("ja", slug)


@app.route("/")
def index_ja():
    return render("ja")


@app.route("/ko")
def index_ko():
    return render("ko")


@app.post("/contact")
def contact():
    f = request.form
    if f.get("website"):  # honeypot
        abort(400)
    if _rate_limited(_ip()):
        abort(429)
    row = {k: f.get(k, "").strip()[:500] for k in
           ("name", "contact", "people", "date", "origin", "destination", "service", "message")}
    if not row["name"] or not row["contact"]:
        abort(400)
    row["lang"], row["at"], row["ip"] = f.get("lang", "ja"), datetime.now().isoformat(timespec="seconds"), _ip()
    _append("inquiries.json", row)
    _mail(f"[KumaTravel] 문의 {row['name']}", "\n".join(f"{k}: {v}" for k, v in row.items()))
    return redirect(_back(row["lang"], "sent=contact") + "#contact")


@app.post("/review")
def review():
    f = request.form
    if f.get("website"):
        abort(400)
    if _rate_limited(_ip()):
        abort(429)
    try:
        rating = max(1, min(5, int(f.get("rating", 5))))
    except ValueError:
        rating = 5
    row = {
        "name": f.get("name", "").strip()[:40], "city": f.get("city", "").strip()[:40],
        "service": f.get("service", "").strip()[:40], "rating": rating,
        "body": f.get("body", "").strip()[:1000], "lang": f.get("lang", "ja"),
        "at": datetime.now().strftime("%Y-%m-%d"), "approved": False,
    }
    if not row["name"] or not row["body"]:
        abort(400)
    _append("reviews.json", row)
    _mail(f"[KumaTravel] 새 후기 {row['name']} ★{rating}", row["body"] + f"\n\n승인: {CFG['site_url']}/admin/reviews")
    return redirect(_back(row["lang"], "sent=review") + "#reviews")


def _back(lang, qs):
    return ("/ko" if lang == "ko" else "/") + "?" + qs


# --- 관리: 후기 승인 (?key=ADMIN_PW) ---
def _auth():
    if request.args.get("key") != os.getenv("ADMIN_PW", "1234"):
        abort(403)


@app.route("/admin/reviews")
def admin_reviews():
    _auth()
    rows = _load("reviews.json")
    key = request.args.get("key")
    items = "".join(
        f"<li>[{'승인' if r['approved'] else '대기'}] ★{r['rating']} {r['name']} ({r['city']}) {r['at']}<br>{r['body']}"
        f"<form method=post action='/admin/reviews/{i}?key={key}' style='display:inline'>"
        f"<button name=approved value={'0' if r['approved'] else '1'}>{'숨김' if r['approved'] else '승인'}</button>"
        f"<button name=delete value=1 onclick=\"return confirm('삭제?')\">삭제</button></form></li>"
        for i, r in enumerate(rows))
    inq = "".join(f"<li>{q['at']} {q['name']} / {q['contact']} / {q['service']} {q['date']} {q['people']}명 "
                  f"{q['origin']}→{q['destination']}<br>{q['message']}</li>" for q in _load("inquiries.json")[::-1])
    return f"<meta charset=utf-8><h2>후기</h2><ul>{items}</ul><h2>문의</h2><ul>{inq}</ul>"


@app.post("/admin/reviews/<int:i>")
def admin_review_set(i):
    _auth()
    with _lock:
        rows = _load("reviews.json")
        if i >= len(rows):
            abort(404)
        if request.form.get("delete"):
            rows.pop(i)
        else:
            rows[i]["approved"] = request.form.get("approved") == "1"
        json.dump(rows, open(os.path.join(DATA, "reviews.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return redirect(f"/admin/reviews?key={request.args.get('key')}")


# --- SEO ---
@app.route("/robots.txt")
def robots():
    return Response(f"User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: {CFG['site_url']}/sitemap.xml\n", mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    u = CFG["site_url"]
    imgs = "".join(f"<image:image><image:loc>{u}/static/img/{n}.webp</image:loc></image:image>" for n, _, _ in GALLERY)
    urls = "".join(
        f"<url><loc>{u}{p}</loc><lastmod>{_lastmod(lang).strftime('%Y-%m-%d')}</lastmod><changefreq>weekly</changefreq>"
        f'<xhtml:link rel="alternate" hreflang="ja" href="{u}/"/>'
        f'<xhtml:link rel="alternate" hreflang="ko" href="{u}/ko"/>'
        f'<xhtml:link rel="alternate" hreflang="x-default" href="{u}/"/>{imgs}</url>'
        for p, lang in (("/", "ja"), ("/ko", "ko")))
    urls += "".join(f"<url><loc>{u}/{s}</loc><lastmod>{_lastmod('ja').strftime('%Y-%m-%d')}</lastmod>"
                    f"<changefreq>weekly</changefreq></url>" for s in LANDINGS)
    xml = ('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
           f"{urls}</urlset>")
    return Response(xml, mimetype="application/xml")


@app.route("/rss")
def rss():
    """네이버 서치어드바이저 제출용. 원페이지라 언어별 메인 2개가 항목."""
    from xml.sax.saxutils import escape
    from email.utils import format_datetime
    u = CFG["site_url"]
    items = ""
    pages = [("/", "ja", I18N["ja"]), ("/ko", "ko", I18N["ko"])] + [
        (f"/{s}", "ja", {**I18N["ja"], **lp}) for s, lp in LANDINGS.items()]
    for path, lang, t in pages:
        paras = t["intro"] + [t["svc1_d"], t["svc2_d"], t["svc3_d"], t["price_rt_note"]] + [f"{q} {a}" for q, a in t["faq"]]
        html = "".join(f"<p>{escape(x)}</p>" for x in paras)
        items += (f"<item><title>{escape(t['meta_title'])}</title><link>{u}{path}</link><guid>{u}{path}</guid>"
                  f"<description>{escape(t['meta_desc'])}</description><content:encoded><![CDATA[{html}]]></content:encoded>"
                  f"<pubDate>{format_datetime(_lastmod(lang).astimezone())}</pubDate></item>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>'
           f"<title>{escape(I18N['ja']['brand'])} / Kuma Travel</title><link>{u}/</link>"
           f"<description>{escape(I18N['ja']['meta_desc'])}</description>{items}</channel></rss>")
    return Response(xml, mimetype="application/rss+xml")


if __name__ == "__main__":
    app.run(debug=True)
