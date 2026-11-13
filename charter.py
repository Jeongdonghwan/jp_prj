"""貸切チャーター(대절) 페이지 조합기 — 지역 가이드 /charter/<id> + 키워드 페이지 /q/<키워드> + 허브 /charter.

사실 재료: 아래 D(지역별 명소·팁) + seo/charter_places.json(서울시청→지역 OSRM 도로 거리·시간) + seo/charter_kw.json(키워드).
재생성: python -I tools/charter_build.py
요금은 사이트에 확정된 것만 쓴다: 서울 시내 반나절 4시간 300,000원 · 하루 8시간 500,000원. 서울 밖은 "距離に応じてお見積り".
다른 교통수단과 비교하지 않는다 (guide.OTHERS 로 demo()가 검사).
"""
import hashlib, json, os, re
from datetime import date, timedelta
import guide
from guide import pick, won, kw_slug, kw_norm, PX

BASE = guide.BASE
HALF, FULL = 300000, 500000
LAUNCH = date.fromisoformat(os.getenv("CHARTER_LAUNCH", "2026-11-13"))
WAVE_DAY = {1: 0, 2: 1, 3: 2, 4: 2}  # 금(오픈일) 묶음 1 → 토 2 → 일 3·4: 주말 안에 전부 공개

# id: n(이름), spot(거리 기준 지점), lat/lng, feat, spots, tip, extra(지역 고유 한 줄), rx(키워드 배정)
D = {
    "dmz": dict(n="DMZ・坡州", spot="臨津閣", lat=37.8896, lng=126.7406, rx=r"dmz|板門店|坡州|非武装|臨津",
                feat="韓国と北朝鮮を隔てる非武装地帯（DMZ）の南側にあたるエリア。臨津江に近づくにつれて、鉄条網や見張り台が見えてきます。",
                spots=["臨津閣（イムジンガク）", "自由の橋", "坡州ヘイリ芸術村", "坡州のアウトレット"],
                tip="第3トンネルや都羅展望台など民間人統制区域の中は、公式の見学ツアーへの申し込みとパスポートが必要です。貸切車では統制区域の外にある臨津閣やヘイリ芸術村、アウトレットを自由に回れます。見学の条件は変わることがあるため、最新の情報をご確認のうえご予約ください。",
                extra="冬の臨津江のほとりは風が強く冷え込むため、防寒着があると安心です。"),
    "nami": dict(n="南怡島・加平", spot="南怡島船着場", lat=37.7909, lng=127.5257, rx=r"南怡島|加平|プチフランス|ナミソム",
                 feat="北漢江に浮かぶ南怡島は、ドラマ『冬のソナタ』のロケ地として知られる島。メタセコイアの並木道が有名で、周辺の加平にはプチフランスやアチムゴヨ樹木園があります。",
                 spots=["南怡島", "プチフランス", "アチムゴヨ樹木園", "加平レールバイク"],
                 tip="南怡島へは加平の船着場から船で渡ります。車は船着場の近くで待機し、島から戻ったら次の目的地へそのまま向かえます。",
                 extra="秋の紅葉と冬の雪景色の時期は特に人が多く、道路も混み合います。"),
    "chuncheon": dict(n="春川", spot="春川駅", lat=37.8848, lng=127.7170, rx=r"春川",
                      feat="江原道の湖に囲まれた街。名物のタッカルビとマッククスの店が集まり、昭陽江の上を歩くスカイウォークもあります。",
                      spots=["春川明洞タッカルビ通り", "昭陽江スカイウォーク", "昭陽江ダム"],
                      tip="南怡島と同じ方面なので、午前に南怡島、午後に春川でタッカルビという組み合わせがしやすいエリアです。",
                      extra="タッカルビは鉄板で焼く店と炭火で焼く店があり、好みの店を探すのも楽しみのひとつです。"),
    "suwon": dict(n="水原", spot="華城行宮", lat=37.2819, lng=127.0137, rx=r"水原",
                  feat="世界遺産の水原華城に囲まれた城郭都市。城壁に沿って歩くと、門や楼閣を巡りながら街を見渡せます。",
                  spots=["水原華城", "華城行宮", "八達門", "水原カルビの店"],
                  tip="華城の城壁は一周すると長いため、車で門の近くまで移動し、見たい区間だけ歩くと体力を使わずに回れます。",
                  extra="名物の水原カルビは骨付きの大きな味付けカルビで、昼食に組み込む方が多い一品です。"),
    "yongin": dict(n="韓国民俗村・エバーランド", spot="韓国民俗村", lat=37.2589, lng=127.1185, rx=r"民俗村|エバーランド",
                   feat="ソウルの南、龍仁にある2つの人気スポット。朝鮮時代の村並みを再現した韓国民俗村と、韓国を代表するテーマパークのエバーランドがあります。",
                   spots=["韓国民俗村", "エバーランド", "水原華城"],
                   tip="韓国民俗村と水原華城は車ですぐの距離で、1日でまとめて回る組み合わせが人気です。エバーランドで閉園近くまで遊ぶ場合は、帰りのお迎え時刻を先にお知らせください。",
                   extra="韓国民俗村では時代劇のロケに使われる町並みの中を、韓服姿で歩くこともできます。"),
    "ganghwa": dict(n="江華島", spot="江華邑", lat=37.7470, lng=126.4880, rx=r"江華島",
                    feat="仁川の北西にある、橋で陸とつながった島。世界遺産の支石墓や古刹・伝灯寺など、韓国の古い歴史が残ります。",
                    spots=["伝灯寺", "江華支石墓", "江華風物市場"],
                    tip="島内のスポットは互いに離れているため、車で順番に回ると短い時間でも主要な場所を見られます。",
                    extra="江華風物市場では、名産の高麗人参やカブのキムチが並びます。"),
    "incheon": dict(n="仁川（チャイナタウン・松島）", spot="仁川チャイナタウン", lat=37.4755, lng=126.6176, rx=r"仁川|チャイナタウン|松島|月尾島",
                    feat="チャジャン麺発祥の地として知られるチャイナタウンと、壁画の並ぶ松月洞童話村、海沿いの月尾島、高層ビルが並ぶ松島がそろう港町。",
                    spots=["仁川チャイナタウン", "松月洞童話村", "月尾島", "松島セントラルパーク"],
                    tip="仁川空港に近いので、出国日に仁川を観光してから空港へ向かうプランも組めます。",
                    extra="チャイナタウンには、チャジャン麺の歴史を紹介する博物館もあります。"),
    "icheon": dict(n="利川・驪州", spot="利川陶芸村", lat=37.2723, lng=127.4350, rx=r"利川|驪州",
                   feat="陶磁器の里として知られる利川と、アウトレットや世宗大王陵（英陵）がある驪州。ソウルから南東へ向かう同じ方面にあります。",
                   spots=["利川陶芸村", "驪州のアウトレット", "世宗大王陵（英陵）"],
                   tip="アウトレットで買い物が増えても、貸切車ならトランクに積んだまま次の場所へ移動できます。",
                   extra="利川は米どころとしても知られ、釜炊きのご飯と小皿料理が並ぶ定食が名物です。"),
    "yangpyeong": dict(n="楊平", spot="両水里", lat=37.5440, lng=127.3180, rx=r"楊平",
                       feat="北漢江と南漢江が合流する川辺の町。朝もやの両水里（ドゥムルモリ）は写真スポットとして人気です。",
                       spots=["両水里（ドゥムルモリ）", "洗美苑", "川沿いのカフェ"],
                       tip="両水里は朝の時間帯の景色が特にきれいなので、早めの出発をおすすめします。",
                       extra="川沿いには景色を眺められる大型カフェが点在し、ドライブの休憩に向いています。"),
    "pocheon": dict(n="抱川", spot="抱川アートバレー", lat=37.9407, lng=127.2218, rx=r"抱川",
                    feat="ソウルの北東にある自然の多いエリア。石切り場を再生した抱川アートバレーや、ハーブアイランドがあります。",
                    spots=["抱川アートバレー", "ハーブアイランド", "山井湖"],
                    tip="見どころが山あいに分かれているため、車で移動すると待ち時間なく次の場所へ向かえます。",
                    extra="抱川アートバレーの天柱湖は、切り立った岩壁に囲まれた湖として写真に人気があります。"),
    "gwangmyeong": dict(n="光明洞窟", spot="光明洞窟", lat=37.4268, lng=126.8663, rx=r"光明洞窟",
                        feat="廃鉱山を再生した洞窟のテーマパーク。坑道の中にワインセラーや光のアート展示があり、ソウルの南西に隣接しています。",
                        spots=["光明洞窟", "洞窟内のワインセラー", "光明の大型ショッピング施設"],
                        tip="洞窟の中は一年を通してひんやりしているので、夏でも羽織るものがあると安心です。",
                        extra="ソウル市内から近く、半日の貸切でも組み込みやすい場所です。"),
    "gangneung": dict(n="江陵", spot="江陵駅", lat=37.7637, lng=128.8995, rx=r"江陵",
                      feat="東海岸の港町。安木海辺のコーヒー通りや、海に面した鏡浦台、日の出の名所・正東津があります。",
                      spots=["安木海辺コーヒー通り", "鏡浦台", "正東津", "江陵中央市場"],
                      tip="ソウルからは片道の運転時間が長いため、1日貸切で朝早めに出発するか、宿泊を含めた行程が向いています。",
                      extra="江陵は「コーヒーの街」と呼ばれ、海を見ながら飲めるカフェが海岸沿いに並びます。"),
    "sokcho": dict(n="束草", spot="束草中央市場", lat=38.2040, lng=128.5910, rx=r"束草|雪岳",
                   feat="雪岳山の玄関口となる東海岸の町。束草中央市場のタッカンジョンや、アバイ村のイカスンデが名物です。",
                   spots=["雪岳山国立公園", "束草中央市場", "アバイ村", "束草海水浴場"],
                   tip="雪岳山まで足を延ばす場合は、ケーブルカーの待ち時間も見込んで行程を組みましょう。",
                   extra="アバイ村へは、渡し船のケッペで渡る昔ながらの風景も見られます。"),
    "pyeongchang": dict(n="平昌", spot="大関嶺", lat=37.6700, lng=128.7060, rx=r"平昌|大関嶺",
                        feat="2018年冬季オリンピックの開催地。大関嶺の羊牧場や、モミの木の並木道が続く月精寺など、高原の自然が広がります。",
                        spots=["大関嶺羊牧場", "月精寺", "五台山"],
                        tip="高原のため冬は雪が多く、気温もソウルより低くなります。冬は暖かい服装でお出かけください。",
                        extra="夏も涼しい日が多く、避暑地として訪れる人が多いエリアです。"),
    "jeonju": dict(n="全州", spot="全州韓屋村", lat=35.8150, lng=127.1530, rx=r"全州",
                   feat="伝統家屋の韓屋が軒を連ねる全州韓屋村と、ビビンバで知られる食の街。",
                   spots=["全州韓屋村", "慶基殿", "殿洞聖堂", "南部市場"],
                   tip="韓屋村の中は歩いて回るエリアです。車は近くで待機するので、韓服を着て散策する間も荷物は車に置いておけます。",
                   extra="南部市場の夜市や、豆もやしのクッパも全州の名物です。"),
    "andong": dict(n="安東", spot="河回村", lat=36.5390, lng=128.5180, rx=r"安東|河回",
                   feat="世界遺産の河回村（ハフェマウル）がある儒教文化の街。安東チムタクや安東焼酎が名物です。",
                   spots=["河回村", "屏山書院", "月映橋", "安東旧市場チムタク通り"],
                   tip="河回村と屏山書院は少し離れているので、車があると両方を無理なく回れます。",
                   extra="河回村では、仮面を使った伝統芸能・河回別神クッ仮面劇の公演が行われることもあります。"),
    "gyeongju": dict(n="慶州", spot="大陵苑", lat=35.8380, lng=129.2120, rx=r"慶州",
                     feat="新羅の都だった古都。仏国寺と石窟庵は世界遺産で、大陵苑の古墳群や、夜景の美しい東宮と月池があります。",
                     spots=["仏国寺", "石窟庵", "大陵苑", "瞻星台", "東宮と月池"],
                     tip="見どころが市内のあちこちに散らばっているため、車で回ると主要なスポットを1日でまとめて見られます。",
                     extra="大陵苑の近くの皇理団ギルには、韓屋を改装したカフェや店が並びます。"),
    "busan": dict(n="釜山", spot="海雲台", lat=35.1587, lng=129.1604, rx=r"釜山",
                  feat="韓国第2の都市で港町。海雲台のビーチ、カラフルな甘川文化村、チャガルチ市場、海辺に建つ海東龍宮寺などがあります。",
                  spots=["海雲台", "甘川文化村", "チャガルチ市場", "海東龍宮寺"],
                  tip="ソウルからは片道の移動が長いため、釜山に泊まる旅程や、釜山市内だけを回る貸切もご相談ください。",
                  extra="海雲台から海東龍宮寺までは海沿いを走るので、車窓の景色も楽しめます。"),
    "daegu": dict(n="大邱", spot="東城路", lat=35.8690, lng=128.5960, rx=r"大邱",
                  feat="韓国南東部の内陸の都市。西門市場の夜市や、近代の建物が残る近代路地、八公山などがあります。",
                  spots=["西門市場", "近代路地", "八公山", "東城路"],
                  tip="市内の見どころと郊外の八公山は離れているので、車で回ると移動の負担が少なくなります。",
                  extra="大邱は夏の暑さで知られ、夏の観光は朝夕の涼しい時間に屋外を回るのがおすすめです。"),
    "gongju": dict(n="公州・扶余", spot="公山城", lat=36.4640, lng=127.1250, rx=r"扶余|公州",
                   feat="百済の都があった2つの町。公山城や宋山里古墳群、扶余の定林寺址などが「百済歴史遺跡地区」として世界遺産に登録されています。",
                   spots=["公山城", "宋山里古墳群", "扶蘇山城", "定林寺址"],
                   tip="公州と扶余は車で行き来できる距離なので、1日で両方の世界遺産を回る行程も組めます。",
                   extra="秋には百済文化祭が開かれ、公州と扶余の町がにぎわいます。"),
    "danyang": dict(n="丹陽", spot="丹陽", lat=36.9840, lng=128.3650, rx=r"丹陽",
                    feat="南漢江沿いの渓谷の町。川に浮かぶ島潭三峰の奇岩や、万川河スカイウォーク、古藪洞窟で知られます。",
                    spots=["島潭三峰", "万川河スカイウォーク", "古藪洞窟"],
                    tip="パラグライダーの体験も人気で、天候によって飛べる時間が変わるため、予定に余裕を持たせると安心です。",
                    extra="名物はニンニクを使った料理で、ニンニク定食を出す店が町に並びます。"),
}
SEOUL = dict(n="ソウル市内", page=("/seoul-charter", "ソウルチャーター車・貸切"),
             spots=["景福宮", "広蔵市場", "明洞", "Nソウルタワー", "ロッテワールドタワー"])
SKIP = r"空港|統営|麗水"  # 공항 대절은 공항 가이드에, 남해안은 당일 대절 범위 밖

_P = os.path.join(BASE, "seo", "charter_places.json")
DIST = json.load(open(_P, encoding="utf-8")) if os.path.exists(_P) else {}
_K = os.path.join(BASE, "seo", "charter_kw.json")
_RAW = json.load(open(_K, encoding="utf-8")) if os.path.exists(_K) else []


def dest_of(kw):
    if re.search(SKIP, kw):
        return None
    return next((i for i, x in D.items() if re.search(x["rx"], kw, re.I)), "seoul")


def hm(m):
    return (f"約{m // 60}時間" + (f"{m % 60}分" if m % 60 else "")) if m >= 60 else f"約{m}分"


def far(i):
    return DIST[i]["min"] > 150  # 편도 2시간 반 넘으면 당일은 하루 대절 전제


PAGES = [{"id": i, "wave": 1 + n % 2} for n, i in enumerate(D)]
BY_ID = {p["id"]: p for p in PAGES}

# 키워드 페이지: 같은 키워드(어순·표기만 다름)는 1페이지, 공항 가이드의 키워드와 겹치면 만들지 않는다
_used = {kw_norm(k["kw"]) for k in guide.KW} | {kw_norm(p["main"]) for p in guide.PAGES} | {kw_norm(s.replace("-", " ")) for s in guide.KW_ALIAS}
KW, KW_ALIAS = [], {}
_seen = {}
for _n, _x in enumerate(_RAW):
    _d = dest_of(_x["kw"])
    _nk = kw_norm(_x["kw"])
    if not _d or _nk in _used or kw_slug(_x["kw"]) in guide.KW_BY or kw_slug(_x["kw"]) in guide.KW_ALIAS:
        continue
    if _nk in _seen:
        KW_ALIAS[kw_slug(_x["kw"])] = _seen[_nk]
        continue
    _seen[_nk] = f"/q/{kw_slug(_x['kw'])}"
    KW.append({"kw": _x["kw"], "slug": kw_slug(_x["kw"]), "parent": _d, "wave": max(BY_ID[_d]["wave"] if _d in BY_ID else 1, 1 + _n % 4), "src": _x["src"]})
KW_BY = {k["slug"]: k for k in KW}
KIDS = {}
for _k in KW:
    KIDS.setdefault(_k["parent"], []).append(_k)


def is_open(p, today=None):
    return (today or date.today()) >= LAUNCH + timedelta(days=WAVE_DAY[p["wave"]])


def open_pages(today=None):
    return [p for p in PAGES if is_open(p, today)]


def path(i):
    return SEOUL["page"][0] if i == "seoul" else f"/charter/{i}"


def label(i):
    return SEOUL["page"][1] if i == "seoul" else f"ソウルから{D[i]['n']}へ貸切チャーター"


def _price(i):
    if i == "seoul":
        return f"半日（4時間）{won(HALF)}・1日（8時間）{won(FULL)}（車1台・定額）"
    return "ソウル発着・距離と時間に応じてお見積り"


def _vehicles(i):
    p = (won(HALF), won(FULL)) if i == "seoul" else ("お見積り", "お見積り")
    return [("車両", "人数", "半日（4時間）", "1日（8時間）"),
            ("スタリア", "6名まで", *p),
            ("ソラティ", "7〜15名", "お問い合わせ", "お問い合わせ")]


def _faqs(i, s):
    """(키워드 패턴, 질문, 답) — 키워드 페이지는 패턴에 맞는 것을 먼저 답한다"""
    if i == "seoul":
        n, where = "ソウル市内", "ソウル市内"
        fee = f"ソウル市内の貸切は、半日（4時間）{won(HALF)}、1日（8時間）{won(FULL)}の定額です（車1台）。時間内なら何か所でも回れます。"
        tm = "ソウル市内は場所によって車で10〜40分ほどの移動が中心です。半日なら3〜4か所、1日なら5〜7か所が回りやすい目安です。"
        trip = "はい。景福宮・広蔵市場・明洞・Nソウルタワーなど、行きたい場所を行きたい順番で回れます。"
    else:
        x, dd = D[i], DIST[i]
        n, where = x["n"], x["n"]
        fee = f"ソウル発着の{n}への貸切は、距離と時間に応じてお見積りします。LINEで日付・人数・回りたい場所をお送りいただければ、総額をお知らせします。"
        tm = f"ソウル市庁から{x['spot']}まで道路距離{dd['km']}km、渋滞がなければ車で{hm(dd['min'])}が目安です。週末や連休は道路が混むため、時間に余裕を持った行程をご提案します。"
        trip = (f"はい。ただし片道{hm(dd['min'])}かかるため、日帰りなら朝早めに出発する1日貸切が前提になります。宿泊を含む行程もご相談ください。" if far(i)
                else f"はい。ソウルのホテルまでお迎えに上がり、{x['spots'][0]}などを回ってホテルまでお送りします。")
    return [
        (r"料金|いくら|値段|相場|費用|安い|定額|比較", f"{n}の貸切チャーターの料金はいくらですか？", fee),
        (r"時間|何時間|距離|行き方|アクセス|ソウルから", f"ソウルから{n}まで車で何時間かかりますか？" if i != "seoul" else "ソウル市内の移動にはどのくらい時間がかかりますか？", tm),
        (r"日帰り|ツアー|1日|半日|モデル|コース|観光", f"{n}は貸切で日帰りできますか？" if i != "seoul" else "ソウル市内を貸切で観光できますか？", trip),
        (r"日本語|LINE|予約|当日|個人", "日本語で予約できますか？",
         "はい。予約から当日の連絡まで、LINEで日本語でやり取りできます。ドライバーも簡単な日本語で対応します。お電話・メールでも受け付けています。"),
        (r"団体|大人数|社員|修学|卒業|ソラティ|15人|大型|ワゴン|ミニバン|スターリア", "何人まで乗れますか？",
         "スタリアは6名まで、ソラティは7〜15名まで乗車できます。人数とお荷物の量をうかがって車両をご案内します。"),
        (r"子連れ|家族|シニア|高齢|車いす", "子連れや年配の家族でも利用できますか？",
         "はい。チャイルドシートは無料でご用意できます。車いすをお使いの方も追加料金なしでご利用いただけ、積み込みや乗り降りはドライバーがお手伝いします。"),
        (r"深夜|早朝|朝", "朝早くや夜遅くの出発もできますか？",
         f"はい。{where}の行程に合わせて、出発時刻とお迎え場所をご相談のうえ決めます。日の出や夜景を見たい場合もお知らせください。"),
        (r"ハイヤー|高級|ジェネシス|リムジン|出張|ビジネス", "ハイヤーのような高級車はありますか？",
         "お一人・少人数向けに、ジェネシスでのVIP送迎もご用意しています。料金はお問い合わせください。"),
        (r"荷物|ショッピング|アウトレット|免税", "観光中、荷物は車に置いておけますか？",
         "はい。観光の間も車は近くで待機するので、買い物の袋や上着は車に置いたまま次の場所へ移動できます。"),
    ]


def _course(i, s):
    if i == "seoul":
        sp = SEOUL["spots"]
        return [f"お迎え：ソウルのホテルまでドライバーがお迎えに上がります。",
                f"午前：{sp[0]}で王宮を見学。周辺の韓服レンタルを利用して写真を撮る方も多いです。",
                f"昼：{sp[1]}で食べ歩き。車は近くで待機しています。",
                f"午後：{pick(s, 'c3', [sp[2], sp[3], sp[4]])}へ。荷物を車に置いたまま身軽に回れます。",
                "お送り：最後はホテルの玄関までお送りします。"]
    x, dd = D[i], DIST[i]
    sp = x["spots"]
    rows = [f"出発：ソウルのホテルまでお迎えに上がり、{x['n']}へ。{x['spot']}まで車で{hm(dd['min'])}が目安です。"]
    for j, a in enumerate(sp[:3]):
        rows.append(f"{['1か所目', '2か所目', '3か所目'][j]}：{a}" + ("。" + x["tip"].split("。")[0] + "。" if j == 0 else "。"))
    rows.append("帰り：同じ車でソウルのホテルまでお送りします。" + ("帰りも長距離になるため、途中で休憩をはさみます。" if far(i) else ""))
    return rows


def _others(i, s, n=5):
    """다른 당일 대절 지역의 거리·시간 — 페이지마다 해시로 골라 숫자가 달라진다"""
    rest = sorted((k for k in D if k != i and k in DIST), key=lambda k: hashlib.md5(f"{s}:o:{k}".encode()).hexdigest())[:n]
    return [f"{D[k]['n']}：ソウル市庁から{DIST[k]['km']}km・車で{hm(DIST[k]['min'])}。{D[k]['feat'].split('。')[0]}。" for k in rest]


def _base(i, s):
    reasons = [
        pick(s, "r1", ["行きたい順番で：決まったツアーの集合時間や人数に合わせる必要がありません。見たい場所に長くいて、興味のない場所は飛ばせます。",
                       "ホテルの玄関から：お迎えはソウルのホテルの玄関前。集合場所まで歩いたり、乗り換えたりする必要がありません。",
                       "自分たちだけの車：ご予約のお客様だけが乗る貸切車です。周りに気を遣わず、会話や休憩も自由です。"]),
        "日本語で相談：行きたい場所や食べたいものをLINEで日本語のまま送るだけで、行程づくりをお手伝いします。",
        pick(s, "r3", ["荷物は車に：上着や買い物の袋は車に置いたまま。身軽に観光できます。",
                       "子連れ・車いすも：チャイルドシートは無料、車いすも追加料金なしでご利用いただけます。",
                       "人数に合わせた車両：スタリアは6名まで、ソラティは7〜15名まで。グループ旅行にも対応します。"]),
    ]
    flow = [("ご相談", "LINE・お電話・メールで、日付・人数・行きたい場所をお送りください。"),
            ("お見積り・ご予約", "行程と料金をご案内し、内容が決まったらご予約完了です。"),
            ("当日", "ソウルのホテルまでドライバーがお迎えに上がります。"),
            ("お送り", "観光のあと、ホテルの玄関までお送りします。")]
    if i == "seoul":
        x = PX["seoul"]
        secs = [("ソウル市内を貸切で回る", [x["feat"] + "景福宮・広蔵市場・明洞・Nソウルタワー・ロッテワールドタワーなど、離れた観光地を車で効率よく回れます。",
                                         f"料金は半日（4時間）{won(HALF)}、1日（8時間）{won(FULL)}の定額（車1台）です。時間内なら何か所でも回れます。"]),
                ("1日貸切のモデルコース", _course(i, s)),
                ("クマトラベルの貸切が便利な理由", reasons)]
        return dict(secs=secs, flow=flow, img=("gyeongbokgung-guard", 600, 800), img_alt="景福宮の守門将交代式")
    x, dd = D[i], DIST[i]
    secs = [(f"{x['n']}はこんなところ", [x["feat"], "主な見どころ：" + "・".join(x["spots"]) + "。", x["extra"]]),
            (f"ソウルから{x['n']}までの距離と時間", [
                f"ソウル市庁から{x['spot']}までは道路距離{dd['km']}km、渋滞がなければ車で{hm(dd['min'])}が目安です。",
                (f"片道の運転時間が長いため、日帰りなら朝早めに出発する1日貸切がおすすめです。宿泊を含む行程もご相談ください。" if far(i)
                 else f"ソウルから日帰りしやすい距離で、{x['spots'][0]}と{x['spots'][1]}を1日で回る行程が組めます。"),
                x["tip"]]),
            (f"{x['n']}を貸切で回るモデルコース", _course(i, s)),
            ("クマトラベルの貸切が便利な理由", reasons),
            ("料金について", [f"ソウル発着の{x['n']}への貸切は、距離と時間に応じてお見積りします。ソウル市内の貸切は半日（4時間）{won(HALF)}、1日（8時間）{won(FULL)}の定額です。",
                            "LINEで日付・人数・回りたい場所をお送りいただければ、行程と総額をお知らせします。"])]
    return dict(secs=secs, flow=flow, img=("solati", 600, 400), img_alt="クマトラベルの貸切車（ソラティ）")


def compose(i):
    """지역 가이드 페이지"""
    x, dd = D[i], DIST[i]
    b = _base(i, i)
    t = f"ソウルから{x['n']}へ貸切チャーター｜日帰りの所要時間・モデルコース｜クマトラベル"
    h1 = f"ソウルから{x['n']}へ貸切チャーター" + pick(i, "h1", ["｜日帰りの所要時間とモデルコース", "｜行きたい順番で回る日帰り旅", "｜ホテルの玄関から日本語で"])
    lead = pick(i, "lead", [
        f"{x['feat'].split('。')[0]}。ソウルのホテルから{x['spot']}まで車で{hm(dd['min'])}。日本語で予約できる貸切車で、{x['spots'][0]}や{x['spots'][1]}を自由に回れます。",
        f"{x['n']}へ、ソウルから貸切車で出かけませんか。{x['spots'][0]}・{x['spots'][1]}など行きたい場所を、行きたい順番で回れます。",
        f"ソウル市庁から{x['spot']}まで道路距離{dd['km']}km。{x['n']}の見どころを貸切車で回る日帰りの行程と、所要時間・料金の目安をまとめました。"])
    box = [("ソウルから", f"{dd['km']}km・車で{hm(dd['min'])}（目安）"), ("料金", _price(i)),
           ("車両", "スタリア6名まで・ソラティ7〜15名"), ("ご予約", "LINEで日本語OK")]
    fq = [(q, a) for _, q, a in _faqs(i, i)]
    b["secs"] = b["secs"] + [("ほかの日帰り貸切先", _others(i, i, 4))]
    return {**b, "title": t, "desc": lead[:150], "h1": h1, "lead": lead, "box": box, "table": _vehicles(i),
            "faq": fq[:6], "parent": ("/charter", "韓国 貸切チャーターガイド"), "c": {"flat": None}, "stype": "貸切チャーター"}


HINT = [(r"料金|いくら|値段|相場|費用|安い|定額", "料金の目安"), (r"日本語", "日本語で予約"), (r"半日", "半日プラン"), (r"1日|一日", "1日プラン"),
        (r"日帰り", "日帰りプラン"), (r"ツアー", "自由に回る貸切ツアー"), (r"行き方|アクセス|ソウルから|距離|時間", "所要時間"),
        (r"子連れ|家族|シニア", "家族旅行"), (r"団体|大人数|社員|修学|卒業", "グループ旅行"), (r"深夜|早朝", "早朝・深夜"),
        (r"予約|当日|LINE|個人", "予約方法"), (r"おすすめ|口コミ|比較|モデル|コース|人気", "おすすめの回り方"),
        (r"ゴルフ|コンサート|K-POP|推し|出張|ビジネス|結婚|病院|美容|免税|カジノ|ショッピング", "目的に合わせた貸切"),
        (r"スターリア|ソラティ|ジェネシス|ワゴン|ミニバン|大型|15人|高級|リムジン", "車両のご案内"), (r"ハイヤー", "ハイヤー"),
        (r"タクシー", "日本語で予約できる貸切車")]


def _place_in(kw):
    """서울 동네 키워드면 guide.PX 의 장소"""
    return next((k for k, rx in PLACES_RX if re.search(rx, kw, re.I)), None)


_ALIAS = {"jongno": "景福宮|北村|益善洞|光化門|鍾路|仁寺洞", "gangnam": "狎鴎亭|カロスキル|新沙|清潭", "hongdae": "延南洞|合井|新村",
          "jamsil": "ロッテワールド", "yeouido": "麻浦", "samseong": "三成|COEX", "seoul-station": "ソウル駅", "itaewon": "梨泰院|南山"}
PLACES_RX = [(k, _ALIAS.get(k, "|".join(PX[k]["n"].split("・")))) for k in PX if k != "seoul"]


def compose_kw(k):
    i, kw, s = k["parent"], k["kw"], k["slug"]
    b = _base(i, s)
    n = SEOUL["n"] if i == "seoul" else D[i]["n"]
    hint = next((h for pat, h in HINT if re.search(pat, kw, re.I)), pick(s, "hint", ["貸切チャーターのご案内", "日帰り貸切の回り方", "料金と所要時間"]))
    fa = _faqs(i, s)
    hits = [(q, a) for pat, q, a in fa if re.search(pat, kw, re.I)]
    secs = [(q, [a]) for q, a in hits[:2]]
    pl = _place_in(kw) if i == "seoul" else None
    if pl:
        x = PX[pl]
        secs.append((f"{x['n']}から貸切で出かける", [x["feat"], f"{x['n']}の見どころ：{x['spots']}。", x["tip"],
                                                f"{x['hotels'].split('・')[0]}など{x['n']}のホテルの玄関までお迎えに上がり、そのまま観光へ向かえます。"]))
    h = lambda key: int(hashlib.md5(f"{s}:{key}".encode()).hexdigest(), 16)
    for j, (t, ps) in enumerate(b["secs"]):
        keep = ps if j < 2 and i != "seoul" else [p for m, p in enumerate(ps) if h(f"{j}:{m}") % 5 < 3] or [ps[h(j) % len(ps)]]  # 지역 고유 사실 2섹션은 통째로
        secs.append((t, keep))
    if i == "seoul":  # 서울 시내 동네 사실 4곳 (페이지마다 해시로 고른다)
        ar = sorted((x for x in PX if x not in ("seoul", pl) and PX[x].get("hotels") and x in dict(PLACES_RX)), key=lambda x: h(f"a:{x}"))[:4]
        secs.append(("貸切で回りやすいソウルのエリア", [f"{PX[x]['n']}：{PX[x]['feat']}見どころは{PX[x]['spots']}。" for x in ar]))
    secs.append(("ほかの日帰り貸切先", _others(i, s, max(5, min(12, 5 + (1300 - sum(len(p) for _, ps in secs for p in ps)) // 60)))))
    lead = (hits[0][1].split("。")[0] + "。" if hits else "") + pick(s, "klead", [
        f"「{kw}」で調べている方へ、{n}の貸切チャーターについて{hint}を中心にまとめました。",
        f"{n}を貸切車で回るときの{hint}を、「{kw}」の答えとしてひと目でわかるように整理しました。",
        f"「{kw}」について、クマトラベルの日本語で予約できる貸切チャーターの内容をご案内します。"])
    used = {q for q, _ in hits[:2]}
    rest = sorted(((q, a) for _, q, a in fa if q not in used), key=lambda x: h(x[0]))
    faq = (hits[2:] + rest)[:5]
    box = ([("ソウルから", f"{DIST[i]['km']}km・車で{hm(DIST[i]['min'])}（目安）")] if i != "seoul" else []) + [
        ("料金", _price(i)), ("車両", "スタリア6名まで・ソラティ7〜15名"), ("ご予約", "LINEで日本語OK")]
    return {**b, "title": f"{kw}｜{hint}｜クマトラベル", "desc": lead[:150], "h1": f"{kw}｜{hint}", "lead": lead, "box": box,
            "secs": secs, "faq": faq, "flow": None, "table": _vehicles(i) if pick(s, "tbl", [0, 1]) else None,
            "parent": (path(i), label(i)), "c": {"flat": None}, "stype": "貸切チャーター"}


def kw_open(k, today=None):
    return is_open(k, today)


def kw_siblings(k, n=8):
    sib = [x for x in KIDS[k["parent"]] if x is not k and kw_open(x)]
    return sorted(sib, key=lambda x: hashlib.md5(f"{k['slug']}:{x['slug']}".encode()).hexdigest())[:n]


def related(i, n=6):
    if i == "seoul":
        return [q["id"] for q in open_pages()][:n]
    me = D[i]
    near = sorted((k for k in D if k != i and BY_ID[k] in open_pages()),
                  key=lambda k: (me["lat"] - D[k]["lat"]) ** 2 + (me["lng"] - D[k]["lng"]) ** 2)
    return near[:n]


def demo():
    today = LAUNCH + timedelta(days=2)
    assert all(i in DIST and DIST[i]["km"] for i in D), [i for i in D if i not in DIST]
    assert not set(KW_BY) & set(guide.KW_BY) and not set(KW_BY) & set(guide.KW_ALIAS)
    for i in D:
        g = compose(i)
        text = g["lead"] + "".join(p for _, ps in g["secs"] for p in ps) + "".join(q + a for q, a in g["faq"])
        assert len(text) > 1300 and not re.search(guide.OTHERS, text + g["title"]), (i, len(text), re.search(guide.OTHERS, text))
    short = []
    for k in KW:
        g = compose_kw(k)
        text = g["lead"] + "".join(p for _, ps in g["secs"] for p in ps) + "".join(q + a for q, a in g["faq"])
        assert "None" not in text and "{" not in text
        assert not re.search(guide.OTHERS, text.replace(k["kw"], "")), (k["kw"], re.search(guide.OTHERS, text.replace(k["kw"], "")))
        if len(text) < 1300:
            short.append((k["kw"], len(text)))
    assert not short, short[:10]
    assert len(open_pages(today)) == len(PAGES) and all(kw_open(k, today) for k in KW)
    from collections import Counter
    print(f"ok {len(PAGES)} charter pages, {len(KW)} keyword pages, {len(KW_ALIAS)} merged", dict(Counter(k["parent"] for k in KW)))


if __name__ == "__main__":
    demo()
