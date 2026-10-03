#!/usr/bin/env python3
"""Blush Tiny Blossoms — static site builder.  Run:  python3 build.py   →  writes ./docs

Everything a non-developer needs to change lives in the SETTINGS and LOOKS blocks below.
"""
import hashlib, html, json, re, shutil
from urllib.parse import quote
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent
SRC, DIST = ROOT / "src", ROOT / "docs"   # GitHub Pages serves the docs/ folder of the main branch

# ───────── SETTINGS: edit these ─────────
SHOP = {
    "name": "Blush Tiny Blossoms",
    "domain": "https://blushtinyblossoms.co.in",
    "instagram": "blushtinyblossoms",
    "whatsapp": "919899090496",   # e.g. "919812345678" (country code, no +). Empty hides every WhatsApp button.
    "currency": "₹",
    "mode": "enquiry",       # "enquiry" now. Switch to "store" once prices and checkoutUrl are set.
    "checkoutUrl": "",       # payment / checkout page, used only in "store" mode
    "email": "enquiry@blushtinyblossoms.co.in",   # empty hides email everywhere
    "hours": "Monday to Saturday, 10 am to 6 pm",   # customer support hours (closed Sundays)
    "city": "Shahpur Jat, New Delhi",
}
# The highlighted note on every look page (title, text). Set NOTICE = None to hide it.
NOTICE = ("Festive delivery update", "Festive ’26 pieces are made in limited numbers. Order early for Diwali: we dispatch within 3–5 business days, and express delivery is available to select cities.")
# Policy numbers used by the FAQ, the Terms page and the "Delivery & returns" panel on every look. Change once here.
POLICY = {
    "free_above": 4000,          # free delivery within India above this order value
    "ship_fee": 100,             # delivery fee below it
    "dispatch": "3–5 business days",
    "deliver": "8–14 business days",
    "metro": "1–2 business days", "other": "2–3 business days",   # transit after dispatch
    "express": "₹300–₹500",
    "cancel_hours": 24,          # cancellation window after payment
    "exchange_days": 7,          # size exchange window after delivery
    "damage_hours": 48,          # report damage within
    "return_process": "2–7 business days",
    "refund": "7–10 business days",
    "custom_from": 1000,         # customisation charge starts at
    "custom_extra": "7–10 days", # extra making time for customised pieces
    "updated": "3 October 2026", # "last updated" date on the Terms page
}
# Sizes, in the order they are shown. Prices come in five bands of two sizes each (see the pricing sheet).
SIZES = ["3–4Y", "4–5Y", "5–6Y", "6–7Y", "7–8Y", "8–9Y", "9–10Y", "10–11Y", "11–12Y", "12–13Y"]
BANDS = ["3–4Y & 4–5Y", "5–6Y & 6–7Y", "7–8Y & 8–9Y", "9–10Y & 10–11Y", "11–12Y & 12–13Y"]

# One dict per look. There is no limit: add a dict here and a photo in src/img-orig/ and the look appears everywhere.
#   id        URL name, and the photo file name: src/img-orig/<id>.jpg. More photos for the gallery: <id>-2.jpg, <id>-3.jpg …
#   prices    five numbers, one per band above (from the "Collection Pricing" Google Sheet). None shows "Price on request".
#   mrp       optional, five numbers: shows a struck-through original price next to the price (for a sale).
#   contents  the pieces in the set, comma separated ("Kurta, sharara"); the look page shows the piece count.
#   soldout   optional list of sizes that are sold out, e.g. ["3–4Y", "12–13Y"].
#   new       optional, True shows a "New" tag on the card.
LOOKS = [
    dict(id="lavender-meadow", name="Lavender Meadow", sil="Sleeveless gingham kurta + tiered sharara", pal="Lavender / Ecru / Zari gold", cat=["sharara"], contents="Kurta, sharara", prices=[6700, 7700, 8200, 8700, 9200], pos="50% 20%",
         fabric="Hand-loomed cotton gingham, gold gota edging", detail="Soft lavender checks layered with oversized wildflower bouquets. Sleeveless A-line kurta with tiered sharara, finished with fine kinari gota.", styling="Bare feet on grass, tiny jhumkis, braided hair."),
    dict(id="blush-tropica", name="Blush Tropica", sil="Peplum strappy top + tiered sharara", pal="Blush / Fern green / Cream", cat=["peplum", "sharara"], contents="Peplum top, sharara", prices=[6700, 7700, 8200, 8700, 9200],
         fabric="Blush pink gingham, tropical botanical print, cotton voile lining", detail="Signature strappy peplum with gathered hem, paired with a three-tier sharara. Hand-printed monstera and hibiscus in sage and rose.", styling="For a poolside mehendi. Add pearl flats."),
    dict(id="nilgiri", name="Nilgiri", sil="Full-sleeve kurta pant with gota", pal="Teal / Bubblegum / Mustard", cat=["kurta"], contents="Kurta, pants", prices=[5700, 6700, 7200, 7700, 8200],
         fabric="Teal cotton, hand-block tropical florals, pink triangle gota", detail="A quiet statement. Full sleeves, straight kurta with contrast pyjama. Inverted pink gota triangles at the hem and a tropical vine print at the border.", styling="Brother-sister twinning ready."),
    dict(id="daffodil-picnic", name="Daffodil Picnic", sil="Ruffle-sleeve peplum + wide palazzo", pal="Peony / Daffodil / Leaf", cat=["peplum"], contents="Peplum top, palazzo", prices=[4500, 5500, 6000, 6500, 7000],
         fabric="Pink gingham, ruffle cap sleeves, daffodil border print", detail="Frill-sleeve peplum that flares like a tea rose. Wide palazzo with a hand-painted daffodil garden running along the hem.", styling="Birthday garden party. Mini potli in ivory."),
    dict(id="gulab-dust", name="Gulab Dust", sil="Embroidered kurta sharara set", pal="Dusty rose / Ivory / Sage", cat=["sharara"], contents="Kurta, sharara", prices=[6700, 7700, 8200, 8700, 9200],
         fabric="Dusty rose handloom, mirror and resham floral embroidery", detail="Our most heirloom piece. Faded rose base with ivory and sage resham buttis, accented with tiny mirrors and French knots."),
    dict(id="rosewood-zari", name="Rosewood Zari", sil="Long-sleeve kurta sharara with sequin neckline", pal="Rosewood / Antique gold", cat=["sharara"], contents="Kurta, sharara", prices=[6700, 7700, 8200, 8700, 9200],
         fabric="Rosewood pink cotton, gold sequin butti, zari yoke", detail="A longer silhouette with full sleeves. Deep neckline densely embroidered in gold sequin, with zari booti scattered across the sharara."),
    dict(id="haldi-orchard", name="Haldi Orchard", sil="Tie-up peplum + booti sharara", pal="Mustard / Marigold / Ecru", cat=["peplum", "sharara"], contents="Peplum top, sharara", prices=[6700, 7700, 8200, 8700, 9200],
         fabric="Mustard yellow cotton, tie-up yoke, hand-embroidered booti", detail="Front tie-up peplum with heavy yoke embroidery and tiny tassels. Sharara covered in all-over miniature floral buttis. Sunlit and festive.", styling="Haldi or Basant. Keep accessories minimal."),
    dict(id="lime-bahaar", name="Lime Bahaar", sil="Yoke-embroidered kurta sharara", pal="Chartreuse / Gulabi / Lime leaf", cat=["sharara"], contents="Kurta, sharara", prices=[6000, 7000, 7500, 8000, 8500],
         fabric="Lime chartreuse cotton, pink gota and yoke embroidery", detail="Unexpected and joyful. Chartreuse kurta with a dense floral yoke and contrast pink gota at the tiered sharara seams. A favourite for photos."),
    dict(id="colorblock-bagh", name="Color Block Bagh", sil="Gingham + ivory embroidered top & skirt", pal="Pink / Chikankari ivory / Garden green", cat=["coord"], contents="Top, skirt", prices=[6000, 7000, 7500, 8000, 8500],
         fabric="Pink gingham, ivory chikankari embroidery, cotton skirt", detail="Playful colorblock. Pink gingham bodice with an ivory embroidered yoke and a full gathered skirt in ivory with gingham facing. Festive but light."),
    dict(id="colorblock-bagh-sunshine", name="Color Block Bagh", variant="Sunshine", sil="Gingham + botanical panel top & skirt", pal="Sunshine / Teal / Ivory", cat=["coord"], contents="Top, skirt", prices=None,   # not in the pricing sheet yet
         fabric="Yellow gingham and teal botanical print cotton, lace trim", detail="The same garden colorblock in sunshine yellow. Gingham and teal botanical panels on the top and gathered skirt, finished with a soft lace hem."),
    dict(id="blush-blossom-dress", name="Blush Blossom Dress", sil="Embellished bodice + tiered tulle dress", pal="Blush / Ivory / Soft gold", cat=["dress"], contents="Dress", prices=[6700, 7700, 8200, 8700, 9200], pos="50% 40%",
         fabric="Blush tulle in gathered tiers, hand-embellished bodice", detail="A cloud of blush tulle. Flutter sleeves and a bodice scattered with hand-embellished flowers, over a full tiered skirt made for twirling.", styling="Birthdays and garden parties."),
    dict(id="little-bloom-dress", name="Little Bloom Dress", sil="Strappy tulle dress with appliqué flowers", pal="Ivory / Lilac / Lemon / Coral", cat=["dress"], contents="Dress", prices=[6700, 7700, 8200, 8700, 9200], pos="50% 35%",
         fabric="Ivory tulle skirt, satin bodice, hand-applied fabric flowers", detail="An ivory tulle dress with pastel flowers scattered across the bodice and skirt, as if they had just drifted down from the garden."),
    dict(id="mint-blossom-lehnga", name="Mint Blossom Lehnga", sil="Embellished choli + flared lehnga", pal="Mint / Soft gold / Rose", cat=["lehenga"], contents="Choli, lehnga", prices=[6700, 7700, 8200, 8700, 9200], pos="50% 30%",
         fabric="Mint lehnga and choli with sequin and bead handwork", detail="A mint choli with delicate handwork and an airy flared lehnga, finished with an embellished waist and a tasselled tie."),
    dict(id="gardenia-bandi-set", name="Gardenia Bandi Set", sil="Kurta pyjama + botanical bandi jacket", pal="Sage / Rose / Fern", cat=["boys"], contents="Kurta, pyjama, bandi jacket", prices=[5300, 6300, 6800, 7300, 7800], pos="50% 30%",
         fabric="Sage kurta and pyjama, rose botanical print bandi", detail="For little brothers. A relaxed sage kurta and pyjama under a rose bandi printed with garden botanicals."),
]
FILTERS = [("all", "All looks", None), ("sharara", "Sharara sets", "lavender-meadow"), ("peplum", "Peplum sets", "daffodil-picnic"), ("kurta", "Kurta sets", "nilgiri"),
           ("coord", "Skirt co-ords", "colorblock-bagh"), ("dress", "Dresses", "blush-blossom-dress"), ("lehenga", "Lehngas", "mint-blossom-lehnga"), ("boys", "Boys", "gardenia-bandi-set")]
FEATURED = ["lavender-meadow", "blush-blossom-dress", "haldi-orchard", "little-bloom-dress"]
INSTA = ["blush-tropica", "lime-bahaar", "colorblock-bagh", "haldi-orchard", "daffodil-picnic", "lavender-meadow"]

# Size chart, from the "Size Chart" tab of the BlushTinyBlossoms Google Sheet.
# Each row: age, then (cm, inches) for height, waist, hip, length, chest.
SIZE_CHART = [
    ("Baby", [
        ("1–3 months",   ("56/62", "24.4"), ("36", "14.1"), ("50", "19.75"), ("32", "12.5"), ("53", "20.75")),
        ("3–6 months",   ("62/68", "26.6"), ("36", "14.1"), ("52", "20.5"), ("34", "13.25"), ("55", "21.5")),
        ("6–9 months",   ("68/74", "29"), ("38", "15"), ("55", "21.5"), ("37", "14.25"), ("57", "22.25")),
        ("9–12 months",  ("74/80", "31.4"), ("40", "15.7"), ("58", "22.75"), ("40", "15.75"), ("59", "23.25")),
        ("12–18 months", ("80/86", "33.6"), ("42", "16.5"), ("60", "23.5"), ("43", "17"), ("61", "24")),
        ("18–24 months", ("86/92", "35.6"), ("43", "16.7"), ("62", "24.5"), ("46", "18"), ("63", "24.75")),
    ]),
    ("Children", [
        ("2–3 years",  ("92/98", "38.4"), ("44", "17.25"), ("64", "25.25"), ("51", "20"), ("65", "25.5")),
        ("3–4 years",  ("98/104", "41"), ("46", "18"), ("66", "26"), ("54", "21.25"), ("68", "26.75")),
        ("4–5 years",  ("104/110", "43.2"), ("48", "18.7"), ("68", "26.75"), ("57", "22.5"), ("71", "28")),
        ("5–6 years",  ("110/116", "45.4"), ("50", "19.75"), ("70", "27.5"), ("60", "23.25"), ("74", "29")),
        ("6–7 years",  ("116/122", "48"), ("52", "20.5"), ("72", "28.25"), ("64", "25.25"), ("77", "30.25")),
        ("7–8 years",  ("122/128", "50.5"), ("54", "21.25"), ("75", "29.5"), ("68.5", "27"), ("80", "31.5")),
        ("8–9 years",  ("128/134", "52.6"), ("56", "22"), ("78", "30.75"), ("73", "28.75"), ("84", "33")),
        ("9–10 years", ("134/140", "55"), ("59", "23.25"), ("81", "32"), ("77.5", "30.5"), ("88", "34.5")),
    ]),
    ("Pre-teens", [
        ("10–11 years", ("140/146", "57.4"), ("62", "24.5"), ("84", "33"), ("82", "32.5"), ("92", "36.25")),
        ("11–12 years", ("146/152", "60"), ("64", "25.25"), ("86", "34"), ("86.5", "34"), ("96", "37.75")),
    ]),
    ("Teens", [
        ("12–13 years", ("152/158", "63"), ("66", "26.5"), ("88", "35"), ("88.5", "35"), ("98", "35")),
        ("13–14 years", ("158/164", "66"), ("68", "27.5"), ("90", "36"), ("91", "36"), ("100", "36")),
    ]),
]
CHART_NOTE = "The size chart above is the average sizing of the garments. For the size of a specific garment, refer to the product description of each item."
# ───────── end of settings ─────────

e = html.escape
BY_ID = {l["id"]: l for l in LOOKS}
for l in LOOKS:
    l.setdefault("pos", "50% 35%")
    l["sizes"] = SIZES
    l["priceBySize"] = {sz: l["prices"][i // 2] for i, sz in enumerate(SIZES)} if l.get("prices") else None
    l["mrpBySize"] = {sz: l["mrp"][i // 2] for i, sz in enumerate(SIZES)} if l.get("mrp") else None
    l.setdefault("soldout", [])
    l.setdefault("contents", "")
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")
def src_img(name):
    for x in IMG_EXT:
        if (SRC / "img-orig" / (name + x)).exists(): return SRC / "img-orig" / (name + x)
    return None
def gallery_names(l):
    """The look's photos: <id>.jpg first, then <id>-2.jpg, <id>-3.jpg … in number order."""
    extra = sorted({int(m[1]) for p in (SRC / "img-orig").iterdir() if (m := re.fullmatch(re.escape(l["id"]) + r"-(\d+)\.(?:jpe?g|png|webp)", p.name, re.I))})
    return [l["id"]] + [f"{l['id']}-{n}" for n in extra]
for l in LOOKS:
    if not src_img(l["id"]): raise SystemExit(f"Missing photo for look '{l['id']}': add src/img-orig/{l['id']}.jpg")
    l["gallery"] = gallery_names(l)
IG = f"https://www.instagram.com/{SHOP['instagram']}/"
WA_NUM = SHOP["whatsapp"]
WA_DISPLAY = (f"+{WA_NUM[:2]} {WA_NUM[2:7]} {WA_NUM[7:]}" if len(WA_NUM) == 12 else f"+{WA_NUM}") if WA_NUM else ""
P = POLICY
DM = f"https://ig.me/m/{SHOP['instagram']}"
DIMS = {}


def full(l): return l["name"] + (f" · {l['variant']}" if l.get("variant") else "")
def rupees(n): return f"{SHOP['currency']}{n:,}"
def price(l): return f"From {rupees(min(l['prices']))}" if l.get("prices") else "Price on request"
def title_html(l): return e(l["name"]) + (f' <em style="color:var(--ink-soft)">{e(l["variant"])}</em>' if l.get("variant") else "")


BLOSSOM = '<svg class="blossom" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="12" cy="5.5" r="3.4"/><circle cx="18.2" cy="10" r="3.4"/><circle cx="15.8" cy="17.2" r="3.4"/><circle cx="8.2" cy="17.2" r="3.4"/><circle cx="5.8" cy="10" r="3.4"/></svg>'
IG_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4.2"/><circle cx="17.4" cy="6.6" r=".9" fill="currentColor" stroke="none"/></svg>'
BAG_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M5 8h14l-1 12H6L5 8z"/><path d="M9 8V6.5a3 3 0 0 1 6 0V8"/></svg>'
RULE = f'<div class="rule" aria-hidden="true" style="color:var(--rose)">{BLOSSOM}</div>'


def img(name, alt, sizes="(max-width:620px) 50vw, (max-width:1000px) 33vw, 25vw", pos=None, eager=False, cls=None):
    w, h = DIMS[name]
    style = f' style="object-position:{pos}"' if pos else ""
    load = ' fetchpriority="high"' if eager else ' loading="lazy" decoding="async"'
    big = f", /img/{name}-1600.webp 1600w" if (DIST / "img" / f"{name}-1600.webp").exists() else ""
    c = f' class="{cls}"' if cls else ""
    return (f'<img{c} src="/img/{name}-960.webp" srcset="/img/{name}-480.webp 480w, /img/{name}-960.webp 960w{big}" sizes="{sizes}" '
            f'width="{w}" height="{h}" alt="{e(alt)}"{style}{load}>')


def price_html(l):
    if not l.get("prices"): return "Price on request"
    lo = min(l["prices"])
    mrp = f' <s>{rupees(min(l["mrp"]))}</s>' if l.get("mrp") and min(l["mrp"]) > lo else ""
    return f"From {rupees(lo)}{mrp}"


def card(l, n=None):
    tag = '<span class="tag">New</span>' if l.get("new") else ('<span class="tag">Sale</span>' if l.get("mrp") else "")
    second = (f'<span class="alt">{img(l["gallery"][1], "", pos=l["pos"])}</span>' if len(l["gallery"]) > 1 else "")
    return (f'<a class="card" href="/looks/{l["id"]}" data-cat="{" ".join(l["cat"])}">'
            f'<div class="arch">{img(l["id"], full(l) + ": " + l["sil"], pos=l["pos"])}{second}{tag}</div>'
            f'<div><h3>{title_html(l)}</h3>'
            f'<p class="sil">{e(l["sil"])}</p><p class="price">{price_html(l)}</p></div>'
            f'<span class="more">View look</span></a>')


FOOT_CATS = "".join(f'<li><a href="/collection?show={k}">{lab}</a></li>' for k, lab, _ in FILTERS[1:5])
NAV = [("/collection", "Collection"), ("/our-story", "Our Story"), ("/size-care", "Size Guide"), ("/faq", "FAQ"), ("/contact", "Contact")]


def layout(path, title, desc, body, og="blush-tropica", active=None, jsonld=None, noindex=False):
    url = SHOP["domain"] + ("" if path == "/" else path)
    links = "".join(f'<a href="{h}"{" aria-current=page" if h == active else ""}>{t}</a>' for h, t in NAV)
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in (jsonld if isinstance(jsonld, list) else [jsonld] if jsonld else []))
    robots = '<meta name="robots" content="noindex">' if noindex else f'<link rel="canonical" href="{url}">'
    return f"""<!doctype html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{robots}
<meta name="theme-color" content="#FFFDFC">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SHOP['name']}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SHOP['domain']}/img/{og}-og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preload" href="/fonts/fraunces-latin-full-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/jost-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/site.css?v={VER}">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="announce">Festive ’26 &nbsp;·&nbsp; The English Garden Edit &nbsp;·&nbsp; Free delivery across India above {rupees(P["free_above"])}</div>
<header class="site-head">
  <div class="wrap">
    <button class="menu-btn" type="button" aria-label="Menu" aria-expanded="false" aria-controls="menu"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><path d="M3 7h18M3 12h18M3 17h18"/></svg></button>
    <nav class="nav left" id="menu" aria-label="Primary">{links}<a class="only-mobile" href="{IG}" target="_blank" rel="noopener">Instagram</a></nav>
    <a class="brand" href="/" aria-label="{SHOP['name']}, home"><img src="/img/logo.png" alt="Blush tiny blossoms" width="{DIMS['logo'][0]}" height="{DIMS['logo'][1]}"></a>
    <nav class="nav right" aria-label="Bag and social">
      <a class="ig-link" href="{IG}" target="_blank" rel="noopener">{IG_ICON}<span>@{SHOP['instagram']}</span></a>
      <a class="bag-link" href="/bag" aria-label="Enquiry bag">{BAG_ICON}<span class="lbl">Bag</span><span class="bag-count" data-n="0">0</span></a>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer>
  <div class="wrap">
    <div class="foot">
      <div>
        <a class="brand" href="/"><img src="/img/logo-full.png" alt="Blush tiny blossoms" width="{DIMS['logo-full'][0]}" height="{DIMS['logo-full'][1]}" loading="lazy"></a>
        <p>Festive wear for little ones, made in limited pieces at our {SHOP['city']} atelier.</p>
      </div>
      <div>
        <h4>Shop</h4>
        <ul><li><a href="/collection">The collection</a></li>{FOOT_CATS}<li><a href="/bag">Enquiry bag</a></li></ul>
      </div>
      <div>
        <h4>Customer care</h4>
        <ul><li><a href="/faq">FAQ</a></li><li><a href="/faq#delivery">Shipping &amp; delivery</a></li><li><a href="/faq#returns">Returns &amp; exchanges</a></li><li><a href="/size-care">Size guide</a></li><li><a href="/terms">Terms &amp; conditions</a></li></ul>
      </div>
      <div>
        <h4>Talk to us</h4>
        <ul>
          {f'<li data-wa hidden><a href="#" target="_blank" rel="noopener">WhatsApp {WA_DISPLAY}</a></li>' if WA_NUM else ""}
          <li><a href="{DM}" target="_blank" rel="noopener">Message on Instagram</a></li>
          {f'<li><a href="mailto:{SHOP["email"]}">{SHOP["email"]}</a></li>' if SHOP["email"] else ""}
          <li><a href="/contact">Send an enquiry</a></li>
          <li><a href="/our-story">Our story</a></li>
        </ul>
        <p class="hours">{SHOP['hours']}</p>
      </div>
    </div>
    <div class="legal"><span>© 2026 {SHOP['name']}</span><span><a href="/terms">Terms</a> · <a href="/faq#privacy">Privacy</a> · Made in India</span></div>
  </div>
</footer>
<script src="/assets/data.js?v={VER}"></script>
<script src="/assets/site.js?v={VER}"></script>
</body>
</html>
"""


STEPS = """<div class="steps">
      <div class="step"><h3>Choose a look</h3><p>Open any look to see its fabric, detailing and the sizes it comes in.</p></div>
      <div class="step"><h3>Message us</h3><p>Add looks to your enquiry bag, or send the look name and your child’s age on WhatsApp or Instagram. We reply to confirm availability.</p></div>
      <div class="step"><h3>Confirm the fit</h3><p>Share height and chest measurements if you are between sizes and we will guide you.</p></div>
      <div class="step"><h3>Delivered to you</h3><p>We confirm dispatch and delivery time on chat before you pay.</p></div>
    </div>"""

CODES = """<div class="codes">
        <div><b>Gingham base</b><span>Lavender, blush and mustard checks</span></div>
        <div><b>Tropical botanical</b><span>Monstera, hibiscus, daffodil</span></div>
        <div><b>Tiered sharara</b><span>Two and three tier flare, made to twirl</span></div>
        <div><b>Gota + mirror</b><span>Fine kinari, triangle gota, shisha</span></div>
        <div><b>Peplum silhouette</b><span>Strappy, ruffle-sleeve, tie-up</span></div>
        <div><b>Sustainable cotton</b><span>Handloom, azo-free dyes</span></div>
      </div>"""

INSTA_HTML = '<div class="insta-grid">' + "".join(
    f'<a href="{IG}" target="_blank" rel="noopener" aria-label="Open Instagram">{{{i}}}</a>' for i in range(len(INSTA))) + "</div>"


def size_chips(): return "".join(f"<span>{s}</span>" for s in SIZES)


def home():
    hero_sizes = "(max-width:820px) 60vw, 30vw"
    body = f"""<section class="hero">
  <div class="wrap">
    <div class="hero-copy">
      <span class="eyebrow">Kids Festive ’26 · Ages 3 to 13</span>
      <h1>Gingham <em>meets</em> gulab.</h1>
      <p class="lede">A garden party of tropical florals blooming on checks, tiered shararas that spin, and gota that catches light like morning dew.</p>
      <p class="body">Festive wear from our Shahpur Jat atelier, cut in soft cottons with hand-printed botanicals and heirloom gota work. Made for twirling at Diwali, mehendi mornings and birthday lawns.</p>
      <div class="hero-cta">
        <a class="btn" href="/collection">View the collection</a>
        <a class="btn ghost" href="/contact">Send an enquiry</a>
      </div>
      <div class="hero-meta"><span>Hand-block florals</span><span>Gota &amp; mirror work</span><span>Softest cottons</span></div>
    </div>
    <div class="hero-art">
      <a class="arch a1" href="/looks/blush-tropica">{img("blush-tropica", "Girl twirling in the Blush Tropica pink gingham peplum and tiered sharara", hero_sizes, eager=True)}<span class="tagchip">Blush Tropica</span></a>
      <div class="col">
        <a class="arch a2" href="/looks/gulab-dust">{img("gulab-dust", "Girl in the Gulab Dust embroidered kurta sharara under a rose arch", hero_sizes, eager=True)}</a>
        <a class="arch a3" href="/looks/mint-blossom-lehnga">{img("mint-blossom-lehnga", "Little girl in the Mint Blossom Lehnga", hero_sizes, pos="50% 22%", eager=True)}</a>
      </div>
    </div>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap">
    {RULE}
    <div class="sec-head" style="margin-top:clamp(40px,6vw,72px)">
      <span class="eyebrow">The English Garden Edit</span>
      <h2>Fresh looks, <em>one garden</em></h2>
      <p>A first look at the edit, with new pieces blooming through the season. Open any piece for fabric, detail and sizes.</p>
    </div>
    <div class="grid">{"".join(card(BY_ID[i]) for i in FEATURED)}</div>
    <p class="center mt"><a class="btn ghost" href="/collection">See the full collection</a></p>
  </div>
</section>

<section class="section story">
  <div class="wrap">
    <div class="arch">{img("rosewood-zari", "Girl in the Rosewood Zari kurta sharara on a rose-lined path", "(max-width:820px) 90vw, 40vw")}</div>
    <div class="story-copy">
      <span class="eyebrow">Collection notes</span>
      <h2>A garden, stitched into <em>festive wear</em></h2>
      <p class="lede">“We wanted Diwali to feel like a picnic in an English garden. Gingham laid on grass, flowers tucked in hair.”</p>
      <p class="body">For Festive 2026 we reimagined our atelier favourites, peplums, shararas and palazzos, in a soft garden palette. Checks in lavender, peony pink and ecru become the canvas, printed over with oversized monstera, hibiscus and daffodil.</p>
      {CODES}
      <p><a class="btn ghost" href="/our-story">Read our story</a></p>
    </div>
  </div>
</section>

<section class="section twin">
  <div class="wrap">
    <div class="twin-copy">
      <span class="eyebrow">For siblings</span>
      <h2>Brother and sister, <em>in bloom together</em></h2>
      <p>Nilgiri carries its teal tropical print across a relaxed kurta and pyjama, and the Gardenia Bandi Set pairs a sage kurta with a rose botanical jacket. Dress them from the same garden without matching them exactly.</p>
      <a class="btn ghost" href="/collection?show=boys">See the boys’ look</a>
    </div>
    <div class="twin-art">
      <a class="arch" href="/looks/nilgiri">{img("nilgiri", "Girl in the teal Nilgiri kurta and pant", "(max-width:820px) 45vw, 25vw")}</a>
      <a class="arch" href="/looks/gardenia-bandi-set">{img("gardenia-bandi-set", "Boy in a sage kurta pyjama with rose botanical bandi jacket", "(max-width:820px) 45vw, 25vw")}</a>
    </div>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">How to order</span>
      <h2>Reserved for you, <em>over a message</em></h2>
    </div>
    {STEPS}
    <div class="care">
      <div>
        <span class="eyebrow">Sizing &amp; make</span>
        <h2>Three to thirteen, <em style="color:#F0B4CC">one relaxed fit</em></h2>
        <p style="margin-top:22px"><a class="btn" style="background:#FFF6F7;color:var(--ink);border-color:#FFF6F7" href="/size-care">Size &amp; care guide</a></p>
      </div>
      <dl>
        <div><dt>Sizes</dt><dd><div class="sizes">{size_chips()}</div>Relaxed fit with side-seam pockets in the shararas. The tiered volume is scaled up for the older sizes.</dd></div>
        <div><dt>Fabric</dt><dd>Cotton bases for the printed sets and tulle for the dresses, with gota, sequin and resham handwork.</dd></div>
        <div><dt>Care</dt><dd>Dry-clean only. Professional dry-cleaning preserves the print and embroidery.</dd></div>
      </dl>
    </div>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">On Instagram</span>
      <h2><em>@{SHOP['instagram']}</em></h2>
      <p>New looks, fittings and behind the seams from the atelier.</p>
    </div>
    {INSTA_HTML.format(*[img(i, "", "(max-width:820px) 33vw, 16vw") for i in INSTA])}
    <p class="center" style="margin-top:34px"><a class="btn ghost" href="{IG}" target="_blank" rel="noopener">Follow on Instagram</a></p>
  </div>
</section>"""
    ld = {"@context": "https://schema.org", "@type": "ClothingStore", "name": SHOP["name"], "url": SHOP["domain"],
          "image": f"{SHOP['domain']}/img/blush-tropica-og.jpg", "logo": f"{SHOP['domain']}/img/logo.png", "sameAs": [IG],
          "address": {"@type": "PostalAddress", "addressLocality": "Shahpur Jat, New Delhi", "addressCountry": "IN"},
          "description": "Festive wear for children aged 3 to 13, made in limited pieces in New Delhi."}
    return layout("/", "Blush Tiny Blossoms · Kids’ festive wear, made in India",
                  "Festive wear for little ones aged 3 to 13. Hand-block florals, gingham and gota work, made in limited pieces at our Shahpur Jat atelier, New Delhi.", body, jsonld=ld)


def collection():
    filt = "".join(
        f'<button class="filter" type="button" data-key="{k}" aria-pressed="{"true" if k == "all" else "false"}">'
        f'<div class="thumb {"" if im else "all"}">{img(im, "", "104px", pos="50% 25%") if im else BLOSSOM}</div><span>{lab}</span></button>'
        for k, lab, im in FILTERS)
    body = f"""<section class="page-head">
  <div class="wrap">
    <span class="eyebrow">The English Garden Edit · Festive ’26</span>
    <h1>Every look, <em>one garden</em></h1>
    <p class="lede">Open a look for fabric, detail and sizes, then add it to your enquiry bag. New pieces are added through the season.</p>
  </div>
</section>
<section class="section" style="padding-top:0">
  <div class="wrap">
    <div class="filters" id="filters" role="group" aria-label="Filter looks by silhouette">{filt}</div>
    <p class="count" id="count" aria-live="polite">{len(LOOKS)} looks</p>
    <div class="grid" id="grid">{"".join(card(l) for l in LOOKS)}</div>
  </div>
</section>"""
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": "The English Garden Edit",
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{SHOP['domain']}/looks/{l['id']}", "name": full(l)} for i, l in enumerate(LOOKS)]}
    return layout("/collection", "The collection · Blush Tiny Blossoms",
                  "Festive looks for children aged 3 to 13: tiered shararas, peplum sets, kurta sets, skirt co-ords, tulle dresses, lehngas and boys’ sets.", body, active="/collection", jsonld=ld)


CHART_COLS = ["Height", "Waist", "Hip", "Length", "Chest"]


def chart_html(groups=None, compact=False):
    """The size chart from the Google Sheet, with a cm / inches switch. groups: names to include (None = all)."""
    body = ""
    for g, rows in SIZE_CHART:
        if groups and g not in groups: continue
        body += f'<tbody><tr class="grp"><th colspan="6" scope="colgroup">{g}</th></tr>'
        for age, *cells in rows:
            body += f'<tr><th scope="row">{age}</th>' + "".join(f'<td><span class="cm">{cm}</span><span class="in">{inch}</span></td>' for cm, inch in cells) + "</tr>"
        body += "</tbody>"
    head = '<thead><tr><th scope="col">Age</th>' + "".join(f'<th scope="col">{c}</th>' for c in CHART_COLS) + "</tr></thead>"
    return (f'<div class="chart" data-unit="cm"><div class="unit" role="group" aria-label="Units">'
            f'<button type="button" data-u="cm" aria-pressed="true">cm</button><button type="button" data-u="in" aria-pressed="false">inches</button></div>'
            f'<div class="chart-scroll"><table class="size-chart{" compact" if compact else ""}">{head}{body}</table></div>'
            f'<p class="hint">{CHART_NOTE}</p></div>')


def delivery_text():
    return (f"<p>Every piece is checked at our atelier and dispatched within {P['dispatch']}. Most orders arrive within {P['deliver']} of purchase.</p>"
            f"<ul><li>Free delivery across India on orders above {rupees(P['free_above'])}; {rupees(P['ship_fee'])} below that.</li>"
            f"<li>Express delivery to select cities, {P['express']}.</li>"
            f"<li>Size exchanges within {P['exchange_days']} days of delivery, subject to availability.</li>"
            f"<li>Returns only for damaged, defective or incorrect pieces, reported within {P['damage_hours']} hours with photos.</li></ul>"
            f'<p><a href="/faq#delivery">Delivery FAQ</a> · <a href="/faq#returns">Returns &amp; exchanges</a></p>')


SHARE_ICONS = {
    "wa": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M4 20l1.3-4A8 8 0 1 1 8.4 19z"/><path d="M9 8.5c0 3.5 3 6.5 6.5 6.5l1-1.6-2-1-1 .8a5 5 0 0 1-2.7-2.7l.8-1-1-2z"/></svg>',
    "fb": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M14 8h3V4.5h-3a4 4 0 0 0-4 4V11H7.5v3.5H10V21h3.5v-6.5H16l.7-3.5h-3.2V8.6c0-.3.2-.6.5-.6z"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a1 1 0 0 1-1 1A16 16 0 0 1 4 5a1 1 0 0 1 1-1z"/></svg>',
    "link": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M10 14a4.5 4.5 0 0 0 6.4 0l3-3a4.5 4.5 0 0 0-6.4-6.4l-1 1"/><path d="M14 10a4.5 4.5 0 0 0-6.4 0l-3 3a4.5 4.5 0 0 0 6.4 6.4l1-1"/></svg>',
}


def look(l, prev, nxt):
    sizes = l["sizes"]
    size_html = ("".join(f'<button type="button" aria-pressed="false"{" disabled" if s in l["soldout"] else ""}>{s}</button>' for s in sizes) if sizes
                 else '<span class="hint">Sizes on request. Tell us your child’s age and we will guide you.</span>')
    url = f"{SHOP['domain']}/looks/{l['id']}"
    g = l["gallery"]
    slides = "".join(f'<button type="button" class="slide" data-i="{i}" aria-label="Open photo {i + 1} of {len(g)}">'
                     f'{img(n, full(l) + (": " + l["sil"] if i == 0 else f", photo {i + 1}"), "(max-width:820px) 100vw, 46vw", pos=l["pos"] if i == 0 else None, eager=i == 0)}</button>'
                     for i, n in enumerate(g))
    thumbs = ("<div class=\"thumbs\" role=\"tablist\" aria-label=\"Photos\">" + "".join(
        f'<button type="button" role="tab" data-i="{i}" aria-selected="{"true" if i == 0 else "false"}" aria-label="Photo {i + 1}">{img(n, "", "84px", pos=l["pos"] if i == 0 else None)}</button>'
        for i, n in enumerate(g)) + "</div>") if len(g) > 1 else ""
    pieces = [x.strip() for x in l["contents"].split(",") if x.strip()]
    contents = (f"<dt>Contents</dt><dd>{len(pieces)} {'piece' if len(pieces) == 1 else 'pieces'}: {e(', '.join(pieces).lower()).capitalize()}</dd>" if pieces else "")
    styling = f'<p class="it">{e(l["styling"])}</p>' if l.get("styling") else ""
    related = [x for x in LOOKS if x["id"] != l["id"] and set(x["cat"]) & set(l["cat"])]
    related = (related + [x for x in LOOKS if x["id"] != l["id"] and x not in related])[:8]
    wa_share = "https://wa.me/?text=" + quote(f"{full(l)} from Blush Tiny Blossoms {url}")
    fb_share = "https://www.facebook.com/sharer/sharer.php?u=" + quote(url)
    mrp = f'<s id="look-mrp">{rupees(min(l["mrp"]))}</s>' if l.get("mrp") else '<s id="look-mrp" hidden></s>'
    save = ""
    if l.get("mrp") and l.get("prices"):
        pct = round(100 * (1 - min(l["prices"]) / min(l["mrp"])))
        save = f'<span class="badge" id="look-save">Sale · Save {pct}%</span>'
    notice = (f'<details class="notice"><summary>{BAG_ICON}<span>{e(NOTICE[0])}</span></summary><p>{NOTICE[1]}</p></details>' if NOTICE else "")
    body = f"""<section class="look pdp" data-look="{l['id']}">
  <div class="wrap">
    <div class="gallery{" multi" if len(g) > 1 else ""}">
      <div class="stage">
        <div class="track" id="track">{slides}</div>
        {'<button type="button" class="nav-arrow prev" aria-label="Previous photo">‹</button><button type="button" class="nav-arrow next" aria-label="Next photo">›</button>' if len(g) > 1 else ""}
      </div>
      {thumbs}
    </div>
    <div class="look-body">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><a href="/collection">Collection</a><span>/</span><span aria-current="page">{e(full(l))}</span></nav>
      <div><h1>{title_html(l)}</h1><p class="sil">{e(l["sil"])}</p></div>
      <div class="pricebox">
        <p class="price"><span id="look-price">{"From " + rupees(min(l["prices"])) if l.get("prices") else "Price on request"}</span> {mrp} {save}</p>
        <p class="tax">Inclusive of all taxes</p>
        <button class="linkbtn guide-btn" type="button" data-open="sizeguide">Size guide</button>
      </div>
      <div>
        <span class="field-label">Age{"" if not sizes else ' · <span id="size-chosen">choose a size</span>'}</span>
        <div class="sizepick boxes" id="look-sizes">{size_html}</div>
      </div>
      <div class="buy">
        <button class="btn" type="button" id="look-add">Add to bag</button>
        <a class="btn ghost" id="look-buy" href="{"#" if WA_NUM else DM}" target="_blank" rel="noopener">Buy it now</a>
        <p class="added" id="look-added" role="status"></p>
      </div>
      {notice}
      <div class="accs">
        <details class="acc"><summary>Product details</summary><div><p>{e(l["detail"])}</p>{styling}<dl class="spec"><dt>Fabric</dt><dd>{e(l["fabric"])}</dd>{contents}<dt>Palette</dt><dd>{e(l["pal"])}</dd><dt>Made in</dt><dd>Our {SHOP['city']} atelier</dd></dl><p class="hint">Each piece is handcrafted, so slight variations in print placement and handwork are part of its charm.</p></div></details>
        <details class="acc"><summary>Care</summary><div><p><b>Dry clean only.</b> Professional dry cleaning keeps the print, gota and embroidery at their best.</p><ul><li>Let it air out after wear before putting it away.</li><li>Store folded in a muslin or cotton bag, away from direct sunlight.</li><li>Keep perfume and deodorant away from the handwork.</li></ul></div></details>
        <details class="acc"><summary>Delivery &amp; returns</summary><div>{delivery_text()}</div></details>
        <details class="acc"><summary>Terms &amp; conditions</summary><div><p>Orders are confirmed once payment is received. Customised pieces and sale pieces are final sale. <a href="/terms">Read the full terms</a>.</p></div></details>
      </div>
      <div class="assist">
        <h2>Shopping assistance &amp; our promise</h2>
        <p>Available in standard sizes and made to measure. For queries or any requests, call or WhatsApp us:</p>
        <div class="assist-box">
          {f'<a data-wa-plain href="https://wa.me/{WA_NUM}" target="_blank" rel="noopener">{SHARE_ICONS["phone"]} {WA_DISPLAY}</a>' if WA_NUM else f'<a href="{DM}" target="_blank" rel="noopener">Message @{SHOP["instagram"]}</a>'}
          {f'<a href="mailto:{SHOP["email"]}">{SHOP["email"]}</a>' if SHOP["email"] else ""}
          <p>Helpline {SHOP['hours']}</p>
          <p class="hint">Prefer Instagram? <a href="{DM}" target="_blank" rel="noopener">Message @{SHOP['instagram']}</a></p>
        </div>
      </div>
      <div class="share"><span>Share with others</span>
        <button type="button" id="copy-link" data-url="{url}" aria-label="Copy link">{SHARE_ICONS['link']}</button>
        <a href="{wa_share}" target="_blank" rel="noopener" aria-label="Share on WhatsApp">{SHARE_ICONS['wa']}</a>
        <a href="{fb_share}" target="_blank" rel="noopener" aria-label="Share on Facebook">{SHARE_ICONS['fb']}</a>
        <span class="added" id="link-copied" role="status"></span>
      </div>
    </div>
  </div>
</section>
<section class="section band">
  <div class="wrap">
    <div class="sec-head rail-head"><div><span class="eyebrow">From the same garden</span><h2>You may also <em>like</em></h2></div>
      <div class="rail-ctl"><button type="button" class="nav-arrow" data-rail="-1" aria-label="Scroll back">‹</button><button type="button" class="nav-arrow" data-rail="1" aria-label="Scroll on">›</button></div></div>
    <div class="rail" id="rail">{"".join(card(x) for x in related)}</div>
  </div>
</section>
<dialog id="sizeguide" class="sheet" aria-labelledby="sg-title">
  <form method="dialog"><button class="close" aria-label="Close">×</button></form>
  <div class="sheet-body">
    <span class="eyebrow">Size guide</span>
    <h2 id="sg-title">Find the right <em>fit</em></h2>
    <p class="hint">{e(full(l))} comes in {sizes[0]} to {sizes[-1]}. Measure your child and compare with the chart. <a href="/size-care#measure">How to measure</a></p>
    {chart_html(["Children", "Pre-teens", "Teens"], compact=True)}
  </div>
</dialog>
<dialog id="lightbox" class="lightbox" aria-label="Photos of {e(full(l))}">
  <form method="dialog"><button class="close" aria-label="Close">×</button></form>
  <img id="lb-img" alt="">
  {'<button type="button" class="nav-arrow prev" data-lb="-1" aria-label="Previous photo">‹</button><button type="button" class="nav-arrow next" data-lb="1" aria-label="Next photo">›</button>' if len(g) > 1 else ""}
</dialog>"""
    ld = {"@context": "https://schema.org", "@type": "Product", "name": full(l), "description": l["detail"], "material": l["fabric"],
          "image": [f"{SHOP['domain']}/img/{l['id']}-og.jpg"] + [f"{SHOP['domain']}/img/{n}-960.webp" for n in g[1:]],
          "brand": {"@type": "Brand", "name": SHOP["name"]}, "category": "Children's festive wear", "url": url}
    if l.get("prices"):
        ld["offers"] = {"@type": "AggregateOffer", "lowPrice": min(l["prices"]), "highPrice": max(l["prices"]), "priceCurrency": "INR", "url": url}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SHOP["domain"] + "/"},
        {"@type": "ListItem", "position": 2, "name": "Collection", "item": SHOP["domain"] + "/collection"},
        {"@type": "ListItem", "position": 3, "name": full(l), "item": url}]}
    return layout(f"/looks/{l['id']}", f"{full(l)} · {l['sil']} · Blush Tiny Blossoms", f"{l['detail']} {l['fabric']}.", body, og=l["id"], active="/collection", jsonld=[ld, crumbs])


def story():
    body = f"""<section class="page-head">
  <div class="wrap">
    <span class="eyebrow">Our story</span>
    <h1>Born from Blush. Inspired by Aryaana. <em>Made for little moments.</em></h1>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap split" style="align-items:center">
    <div class="duo">
      <div class="arch">{img("blush-blossom-dress", "Little girl in the Blush Blossom Dress at a garden party", "(max-width:820px) 45vw, 24vw", pos="50% 30%")}</div>
      <div class="arch">{img("gulab-dust", "Girl in the Gulab Dust embroidered kurta sharara", "(max-width:820px) 45vw, 24vw")}</div>
    </div>
    <div class="story-copy">
      <span class="eyebrow">How it began</span>
      <p class="body">For 15 years, Blush has been creating Indian and formal wear for women at <strong>BLUSH Kanak Chandhok, Shahpur Jat</strong>.</p>
      <p class="lede">Over the years, our clients often asked, “When are you going to make something for our little ones?”</p>
      <p class="body">Then came Aryaana — our little muse, who wore her mother’s creations for festivals and celebrations and received endless compliments.</p>
      <p class="body">Soon, friends and clients began asking for outfits for their little girls, and for beautiful mother-daughter twinning moments.</p>
      <p class="body">And that’s how <strong>Blush Tiny Blossoms</strong> came to life — a little world of joyful, elegant and beautifully crafted outfits, made for the little girls who make every celebration brighter.</p>
      <h2 style="font-size:clamp(1.5rem,2.6vw,2.1rem);margin-top:6px">For twirls, togetherness and <em>memories that last a lifetime.</em></h2>
    </div>
  </div>
</section>

<section class="section band">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">What we care about</span><h2>Three things, <em>every piece</em></h2></div>
    <div class="values">
      <div class="value" style="color:var(--rose)">{BLOSSOM}<h3 style="color:var(--ink)">Soft first</h3><p>Fabrics chosen to sit gently on young skin, through a long evening of celebrations.</p></div>
      <div class="value" style="color:var(--rose)">{BLOSSOM}<h3 style="color:var(--ink)">Made to move</h3><p>A relaxed fit, side-seam pockets in the shararas and tiers that are cut to twirl. Nothing stiff, nothing scratchy.</p></div>
      <div class="value" style="color:var(--rose)">{BLOSSOM}<h3 style="color:var(--ink)">Handwork that shows</h3><p>Gota, sequin and resham handwork, placed where it catches the light and kept away from where it would bother.</p></div>
    </div>
  </div>
</section>

<section class="section story" style="background:none">
  <div class="wrap">
    <div class="arch">{img("rosewood-zari", "Girl in the Rosewood Zari kurta sharara on a rose-lined path", "(max-width:820px) 90vw, 40vw")}</div>
    <div class="story-copy">
      <span class="eyebrow">Festive ’26 · collection notes</span>
      <h2>The English <em>Garden Edit</em></h2>
      <p class="lede">“We wanted Diwali to feel like a picnic in an English garden. Gingham laid on grass, flowers tucked in hair.”</p>
      <p class="body">For Festive 2026 we reimagined our atelier favourites, peplums, shararas and palazzos, in a soft garden palette. Checks in lavender, peony pink and ecru become the canvas. They are sun-washed, never stark, and printed over with oversized monstera, hibiscus and daffodil.</p>
      {CODES}
    </div>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap cta-band">
    {RULE.replace('class="rule"', 'class="rule" style="width:100%"', 1)}
    <h2 style="margin-top:20px">Come walk <em>the garden</em></h2>
    <div class="hero-cta"><a class="btn" href="/collection">View the collection</a><a class="btn ghost" href="/contact">Talk to us</a></div>
  </div>
</section>"""
    return layout("/our-story", "Our story · Blush Tiny Blossoms",
                  "Born from Blush, the women’s wear label at Shahpur Jat, and inspired by Aryaana: how Blush Tiny Blossoms came to make festive wear for little ones.", body, og="rosewood-zari", active="/our-story")


def _wa(text="WhatsApp"):
    return f'<a href="https://wa.me/{WA_NUM}" target="_blank" rel="noopener">{text} {WA_DISPLAY}</a>' if WA_NUM else f'<a href="{DM}" target="_blank" rel="noopener">Instagram</a>'


def faq_sections():
    fa, fee = rupees(P["free_above"]), rupees(P["ship_fee"])
    contact = _wa("WhatsApp")
    email = f', email <a href="mailto:{SHOP["email"]}">{SHOP["email"]}</a>' if SHOP["email"] else ""
    return [
        ("ordering", "Ordering", [
            ("How do I place an order?", f'Choose a look, pick a size and add it to your <a href="/bag">bag</a>. Send the bag to us on WhatsApp or Instagram in one tap. We confirm availability, fit and delivery, then share a secure payment link. Your order is confirmed once payment is received.'),
            ("Do I need an account?", "No. There is no account or sign-up. Your bag is saved on your device and your order is confirmed over chat."),
            ("Can I get help placing my order?", f"Of course. Message us on {contact} and we will help you choose the look and size."),
            ("Can I amend my order?", "You can change looks or sizes until payment is made. Once an order is confirmed and goes into finishing at the atelier, we are unable to amend it."),
            ("Can I cancel my order?", f"Message us within {P['cancel_hours']} hours of payment and we will cancel it. After that the piece is being prepared for you, so cancellations are not possible."),
            ("Can I order a look or size that is sold out?", f"Often, yes. Send us the look name and the size you need on {contact}. Many pieces can be made again in limited numbers."),
            ("Do prices vary with size?", "Yes. Each look is priced in five size bands, from 3–4Y up to 12–13Y, because the larger sizes use more fabric and handwork. Pick a size on any look to see its price."),
            ("How can I update my delivery address?", "Tell us as soon as possible. We can change the address any time before the order is dispatched."),
            ("How can I track my order?", "Once your order is dispatched we send you the tracking link on WhatsApp or by message."),
        ]),
        ("delivery", "Shipping & delivery", [
            ("How long will my order take to arrive?", f"We dispatch within {P['dispatch']}. Delivery time depends on your location and the courier, but most orders arrive within {P['deliver']} of purchase."),
            ("What are the delivery charges?", f"Free delivery across India on orders above {fa}. A {fee} delivery fee applies below that."),
            ("How long does delivery take after dispatch?", f"Metro cities: {P['metro']}. Other regions: {P['other']}."),
            ("Do you offer express delivery?", f"Yes, to select locations, at {P['express']} depending on the city. Ask us when you order."),
            ("Do you deliver in Delhi the same day?", f"For select ready pieces, yes, and you can also collect from our {SHOP['city']} atelier by appointment. Message us to arrange."),
            ("Do you ship internationally?", "Not yet. We deliver across India. If you would like a piece sent abroad, message us and we will see what we can arrange."),
            ("What if I entered the wrong address?", "Please check your address before you pay. We are not responsible for failed deliveries caused by an incorrect or incomplete address."),
            ("What happens if a parcel is refused at delivery?", "If a parcel is refused and returned to us, we are unable to offer a full refund; delivery charges both ways are deducted."),
            ("Do you refund for courier delays?", "We cannot refund for delays caused by courier partners, but we will follow up and keep you updated until your parcel arrives."),
        ]),
        ("returns", "Returns & exchanges", [
            ("Can I return my order?", f"Returns are accepted only for damaged, defective or incorrect pieces. For a different size, we offer an exchange within {P['exchange_days']} days of delivery, subject to availability."),
            ("What condition should an exchange be in?", "Unworn, unwashed, with all tags and the original packaging."),
            ("What if my piece arrives damaged?", f"Message us within {P['damage_hours']} hours of delivery with photos of the piece and the packaging (an unboxing video helps). We will replace it or refund you."),
            ("How long does a return take?", f"Returns and exchanges are processed within {P['return_process']} of the piece reaching us."),
            ("Can I return a customised piece?", "No. Customised pieces are made to your measurements and are not eligible for return or exchange, unless they arrive damaged or incorrect."),
            ("What if my parcel is lost after delivery?", "Once a parcel is marked delivered by the courier, we cannot take responsibility for it being lost or stolen, but we will help you raise it with the courier."),
        ]),
        ("payments", "Payments & refunds", [
            ("Which payment methods do you accept?", "UPI, bank transfer (NEFT/IMPS), and debit cards, credit cards and net banking from Indian banks through a secure payment link."),
            ("Do you accept international cards?", "Not at the moment. We can accept an international bank transfer on request."),
            ("Money was deducted but my order isn't confirmed. What do I do?", f"Send us the transaction ID, payment reference, date and the phone number you used on {contact}. We will check and confirm, or refund it."),
            ("When will I get my refund?", f"Approved refunds go back to the original payment method within {P['refund']}. We let you know on WhatsApp or by email once it is processed."),
        ]),
        ("custom", "Customisation & styling", [
            ("Can you make a size to my child's measurements?", f"Yes, for select looks. Customisation starts at {rupees(P['custom_from'])} per request and adds about {P['custom_extra']} to the making time. We do recommend our standard sizing, which is carefully graded."),
            ("Can I get a matching outfit for myself?", f"Yes. Blush Tiny Blossoms grew out of BLUSH, our women’s label in {SHOP['city']}, so mother–daughter twinning is close to our heart. Message us and we will create a coordinating look for you."),
            ("Can you help me style a look?", f"Yes. Book a call or a visit to the atelier on {contact} and we will help you put the look together for the occasion."),
            ("Do you alter pieces after delivery?", "We don't offer alterations after delivery. If you are unsure about fit, ask us before ordering and we will guide you, or customise the size."),
        ]),
        ("sizing", "Sizing", [
            ("Which sizes do you make?", f"Ten sizes, from {SIZES[0]} to {SIZES[-1]}. Most looks are available in all of them."),
            ("How do I find the best size for my child?", 'Measure your child and compare with our <a href="/size-care">size guide</a>, which is also on every look. If they are between sizes, choose the larger one, or send us height and chest measurements and we will guide you.'),
            ("What size should I choose for a gift?", "We recommend one size up, so it fits comfortably for longer."),
            ("Why are the larger sizes priced higher?", "Sizes from 7–8Y upwards use more fabric and more handwork, so they are priced in higher bands."),
        ]),
        ("product", "About our pieces", [
            ("Why doesn't my piece look exactly like the photo?", "Every piece is handcrafted, with hand-printed and hand-embroidered details, so no two are exactly alike. Colours can also look slightly different depending on lighting and your screen."),
            ("How should I care for my piece?", "Dry clean only. Professional dry cleaning preserves the print, gota and embroidery. Air it after wear and store it folded in a cotton bag."),
            ("Where are your pieces made?", f"At our atelier in {SHOP['city']}, where every piece is cut, embroidered and finished in limited numbers."),
        ]),
        ("shopping", "Shopping with us", [
            ("How do I contact you?", f"{contact}, or message us on <a href=\"{DM}\" target=\"_blank\" rel=\"noopener\">Instagram @{SHOP['instagram']}</a>{email}."),
            ("When are you available?", f"{SHOP['hours']}. We are closed on Sundays and reply to messages the next working day."),
            ("Can I visit you?", f"Yes. Our atelier is at BLUSH Kanak Chandhok, {SHOP['city']}. Message us to book a visit."),
            ("Where else can I find your pieces?", f"We take part in exhibitions through the year and post every date on <a href=\"{IG}\" target=\"_blank\" rel=\"noopener\">Instagram</a>."),
            ("Have a suggestion or something you'd love us to make?", "We would love to hear it. Tell us on WhatsApp or Instagram."),
        ]),
        ("sale", "Sale terms", [
            ("Are sale pieces final sale?", "Yes. Pieces bought in a sale or from an archive edit cannot be returned, exchanged or cancelled."),
            ("Can I use a promo code on sale pieces?", "Promotional codes are valid for a limited period and cannot be combined with other offers or used on sale pieces."),
            ("How long are sale prices valid?", "Only during the stated sale period, and while stock lasts. We may cancel and refund an order if a piece is no longer available."),
            ("What if a sale piece arrives damaged?", "Message us within 7 days of delivery with photos and we will make it right."),
        ]),
        ("privacy", "Your privacy", [
            ("What information do you collect?", "Only what we need to fulfil your order: your name, phone number, delivery address and, if you share it, your email. Payments are handled by our payment provider; we never see or store your card details."),
            ("How is it used?", "To confirm and deliver your order, handle exchanges, and, only if you agree, tell you about new collections. We never sell your details."),
            ("What does the website store?", "Your bag is saved in your own browser so it is there when you come back. The site uses no advertising trackers."),
        ]),
    ]


def faq_page():
    secs = faq_sections()
    chips = "".join(f'<a href="#{i}">{t}</a>' for i, t, _ in secs)
    blocks = "".join(f'<section class="faq-sec" id="{i}" aria-labelledby="h-{i}"><h2 id="h-{i}">{e(t)}</h2><div class="faq">' +
                     "".join(f"<details><summary>{e(q)}</summary><p>{a}</p></details>" for q, a in qs) + "</div></section>" for i, t, qs in secs)
    body = f"""<section class="page-head">
  <div class="wrap">
    <span class="eyebrow">Help</span>
    <h1>Questions, <em>answered</em></h1>
    <p class="lede">Ordering, delivery, sizing and care. Can’t find what you need? {_wa("WhatsApp us on")}.</p>
  </div>
</section>
<section class="section" style="padding-top:0">
  <div class="wrap faq-wrap">
    <nav class="faq-nav" aria-label="FAQ sections">{chips}</nav>
    <div>{blocks}</div>
  </div>
</section>"""
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for _, _, qs in secs for q, a in qs]}
    return layout("/faq", "FAQ · Blush Tiny Blossoms", "Ordering, delivery, returns, sizing, payments and care for Blush Tiny Blossoms festive wear.", body, og="haldi-orchard", active="/faq", jsonld=ld)


def terms_page():
    fa = rupees(P["free_above"])
    reach = (f'WhatsApp {WA_DISPLAY}' if WA_NUM else "") + (f', email {SHOP["email"]}' if SHOP["email"] else "") + f', Instagram @{SHOP["instagram"]}'
    T = [
        ("About these terms", f"<p>These terms apply to every purchase from {SHOP['name']} (“we”, “us”), whether you order through this website, WhatsApp, Instagram or at our atelier. By placing an order or using this site you agree to them.</p>"),
        ("Electronic communications", "<p>When you visit this site or message us on WhatsApp, Instagram or email, you consent to receive communications from us electronically. Order confirmations, payment links and updates sent this way satisfy any legal requirement that they be in writing.</p>"),
        ("Orders and cancellations", f"<p>An order is confirmed only when we have received full payment. We may decline or cancel an order at our discretion, for example if a piece is no longer available, in which case any payment is refunded in full.</p><p>You may cancel within {P['cancel_hours']} hours of payment. After that the piece is being prepared for you and the order cannot be cancelled or modified. Customised orders cannot be cancelled once confirmed.</p>"),
        ("Prices and payment", f"<p>Prices are in Indian Rupees and include applicable taxes. Prices vary by size band, as shown on each look. Delivery is free within India above {fa}; below that a delivery fee of {rupees(P['ship_fee'])} applies. We may change prices at any time, but the price confirmed at payment is the price you pay.</p>"),
        ("Returns, exchanges and refunds", f"<p>Size exchanges are accepted within {P['exchange_days']} days of delivery, subject to availability, for pieces that are unworn, unwashed and in their original packaging with tags. Returns are accepted only for pieces that arrive damaged, defective or incorrect, reported within {P['damage_hours']} hours of delivery with photos.</p><p>Gift cards, customised and personalised pieces, and sale pieces are not returnable. Approved refunds are made to the original payment method within {P['refund']}.</p>"),
        ("Sale and archive pieces", "<p>Pieces from a sale or an archive edit may come from past collections and can carry minor imperfections, reflected in the reduced price. They are final sale: no returns, exchanges or cancellations. Quantities are limited and styles will not be restocked. If a cart mixes sale and full-price pieces, the whole order follows the full-price dispatch timeline.</p>"),
        ("Customisation", f"<p>Customised sizes are made to the measurements you give us. Charges start at {rupees(P['custom_from'])} per request and making takes about {P['custom_extra']} longer. Please check measurements carefully; customised pieces cannot be returned or exchanged unless they arrive damaged or incorrect.</p>"),
        ("Shipping", f"<p>We dispatch within {P['dispatch']} and most orders arrive within {P['deliver']} of purchase, depending on the product and your location. We are not responsible for delays caused by couriers, incomplete or incorrect address details, or circumstances beyond our control. For anything urgent, contact us on {reach}.</p>"),
        ("Customs and taxes", "<p>We currently deliver within India. If we agree to send an order abroad, any customs duties and taxes charged by the destination country are payable by you. Please check with your local customs office.</p>"),
        ("Copyright and our prints", f"<p>All content on this site, including text, photographs, graphics and logos, belongs to {SHOP['name']}. All designs, patterns, prints and creative works are our intellectual property and are protected by copyright law. They may not be copied, reproduced, distributed, modified or used, commercially or personally, without our written consent. Buying a piece does not transfer the copyright in its print or design. Unauthorised use may lead to legal action. For licensing, contact us.</p>"),
        ("Privacy and personal data", '<p>We collect only what we need to fulfil your order and keep it safe with reasonable measures, though no system is completely secure. We never sell your details. See <a href="/faq#privacy">Your privacy</a> for more. By using this site you consent to this.</p>'),
        ("Product appearance", "<p>Our pieces are handcrafted, so slight variations in colour, print placement and handwork are natural and are not defects. Colours may also appear different on screen.</p>"),
        ("Disclaimers and limitation of liability", "<p>We do not guarantee that this site will be uninterrupted or error-free. To the extent permitted by law, products are provided without warranties beyond those stated here, and we are not liable for indirect, incidental or consequential loss arising from use of the site or our products.</p>"),
        ("Governing law", "<p>These terms are governed by the laws of India. Any dispute is subject to the exclusive jurisdiction of the courts in New Delhi.</p>"),
        ("Changes to these terms", "<p>We may update these terms at any time. The version on this page at the time of your order applies to that order. Continued use of the site means you accept the revised terms.</p>"),
        ("Contact", f"<p>{e(SHOP['name'])}, {SHOP['city']}. {reach}. {SHOP['hours']}.</p>"),
    ]
    toc = "".join(f'<li><a href="#t{i + 1}">{e(t)}</a></li>' for i, (t, _) in enumerate(T))
    sections = "".join(f'<section id="t{i + 1}"><h2><span>{i + 1:02d}</span>{e(t)}</h2>{b}</section>' for i, (t, b) in enumerate(T))
    body = f"""<section class="page-head">
  <div class="wrap">
    <span class="eyebrow">Legal</span>
    <h1>Terms &amp; <em>conditions</em></h1>
    <p class="lede">Last updated {P['updated']}.</p>
  </div>
</section>
<section class="section" style="padding-top:0">
  <div class="wrap faq-wrap">
    <nav class="faq-nav toc" aria-label="Contents"><ol>{toc}</ol></nav>
    <div class="terms">{sections}</div>
  </div>
</section>"""
    return layout("/terms", "Terms & conditions · Blush Tiny Blossoms", "Orders, payment, delivery, returns, exchanges, customisation and copyright terms for Blush Tiny Blossoms.", body, active=None)


def size_care():
    sizes_row = "".join(f"<span>{s}</span>" for s in SIZES)
    body = f"""<section class="page-head">
  <div class="wrap">
    <span class="eyebrow">Size guide</span>
    <h1>Find the right <em>fit</em></h1>
    <p class="lede">Measure your child, then compare with the chart. Our looks come in {SIZES[0]} to {SIZES[-1]}, cut with room to move.</p>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap">
    <div class="sizes ours"><span class="field-label">Our sizes</span>{sizes_row}</div>
    {chart_html()}
  </div>
</section>

<section class="section band" id="measure">
  <div class="wrap split">
    <div>
      <h2>How to <em>measure</em></h2>
      <ol class="measure">
        <li><b>Height</b><span>Standing straight against a wall, without shoes, from the floor to the top of the head.</span></li>
        <li><b>Chest</b><span>Around the fullest part of the chest, under the arms, with the tape level and comfortably loose.</span></li>
        <li><b>Waist</b><span>Around the natural waist, where the sharara or pyjama will sit.</span></li>
        <li><b>Hip</b><span>Around the fullest part of the hips, feet together.</span></li>
        <li><b>Length</b><span>From the highest point of the shoulder, next to the neck, down to where the garment should end.</span></li>
      </ol>
    </div>
    <div>
      <h2>Fit <em>tips</em></h2>
      <ul class="tips">
        <li>Between two sizes? Choose the larger one.</li>
        <li>Buying a gift? Go one size up.</li>
        <li>Shararas and lehngas sit at the waist and are cut with tiered volume, scaled up for the older sizes.</li>
        <li>Still unsure? Send us height and chest with your child’s age and we will guide you before you pay.</li>
      </ul>
      <p style="margin-top:22px"><a class="btn ghost" href="/contact">Ask about sizing</a></p>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="care" style="margin-top:0">
      <div>
        <span class="eyebrow">Fabric &amp; care</span>
        <h2>Looked after, <em style="color:#F0B4CC">it lasts</em></h2>
      </div>
      <dl>
        <div><dt>Fabric</dt><dd>Cotton bases for the printed sets and tulle for the dresses, with gota, sequin and resham handwork.</dd></div>
        <div><dt>Care</dt><dd>Dry clean only. Professional dry cleaning preserves the print and embroidery. Store folded in a cotton bag, away from sunlight.</dd></div>
        <div><dt>Fit</dt><dd>Relaxed through the body, with tiered volume in the shararas.</dd></div>
      </dl>
    </div>
    <p class="center mt"><a class="btn ghost" href="/faq#sizing">Sizing questions</a></p>
  </div>
</section>"""
    return layout("/size-care", "Size guide · Blush Tiny Blossoms",
                  "Size chart in cm and inches for babies, children, pre-teens and teens, how to measure your child, and care for Blush Tiny Blossoms festive wear.", body, og="lavender-meadow", active="/size-care")


def contact():
    opts = '<option value="">The whole collection</option>' + "".join(f'<option value="{l["id"]}">{e(full(l))}</option>' for l in LOOKS)
    sz = '<option value="">Not sure yet</option>' + "".join(f"<option>{s}</option>" for s in SIZES)
    body = f"""<section class="page-head">
  <div class="wrap">
    <span class="eyebrow">Contact</span>
    <h1>Say <em>hello</em></h1>
    <p class="lede">We take orders over a message, so you always speak to a person who knows the pieces.</p>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap">
    <div class="ways">
      <div class="way" data-wa hidden><span class="eyebrow">WhatsApp</span><h3>Chat on WhatsApp</h3><p>The quickest way to reach us. Send a message and we will take it from there.</p><a class="btn" href="#" target="_blank" rel="noopener">WhatsApp us</a></div>
      <div class="way"><span class="eyebrow">Instagram</span><h3>Message us</h3><p>See new looks and fittings, and message us with the look name and your child’s age.</p><a class="btn ghost" href="{DM}" target="_blank" rel="noopener">Open Instagram chat</a></div>
      <div class="way"><span class="eyebrow">Atelier</span><h3>Shahpur Jat, New Delhi</h3><p>Where every piece is cut, embroidered and finished, in limited numbers.</p><a class="btn ghost" href="/our-story">Our story</a></div>
    </div>
  </div>
</section>

<section class="section band">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Send an enquiry</span><h2>Tell us what you <em>need</em></h2><p>Fill this in and we will write the message for you, ready to send on WhatsApp or Instagram.</p></div>
    <div class="composer">
      <form class="form" id="enquiry" novalidate>
        <label>Your name<input name="name" type="text" autocomplete="name"></label>
        <label>Child’s age<input name="age" type="text" inputmode="text" placeholder="e.g. 5 years"></label>
        <label>Look<select name="look">{opts}</select></label>
        <label>Size<select name="size">{sz}</select></label>
        <label class="full">Needed by<input name="date" type="date"></label>
        <label class="full">Anything else<textarea name="note" placeholder="Occasion, measurements, questions"></textarea></label>
      </form>
      <aside class="preview" aria-live="polite">
        <span class="eyebrow">Your message</span>
        <div class="msg" id="enq-msg"></div>
        <div class="dlg-cta">
          <a class="btn" id="enq-wa" data-msg="1" href="#" target="_blank" rel="noopener" hidden>Send on WhatsApp</a>
          <button class="btn ghost" type="button" id="enq-copy" data-label="Copy message">Copy message</button>
          <a class="btn ghost" href="{DM}" target="_blank" rel="noopener">Open Instagram chat</a>
        </div>
        <p class="hint">Nothing is sent from this page. Your message goes only when you paste it in the chat.</p>
      </aside>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">How to order</span><h2>Reserved for you, <em>over a message</em></h2></div>
    {STEPS}
  </div>
</section>"""
    return layout("/contact", "Contact · Blush Tiny Blossoms",
                  "Enquire about Blush Tiny Blossoms festive wear on Instagram. Tell us the look, your child’s age and when you need it.", body, og="daffodil-picnic", active="/contact")


def bag():
    body = f"""<section class="page-head">
  <div class="wrap">
    <span class="eyebrow">Enquiry bag</span>
    <h1>Your <em>looks</em></h1>
    <p class="lede">Send everything in one message. We reply to confirm availability and delivery.</p>
  </div>
</section>
<section class="section" style="padding-top:0">
  <div class="wrap" id="bag-root"><noscript><p class="center">Please enable JavaScript to use the enquiry bag, or <a href="{DM}">message us on Instagram</a>.</p></noscript></div>
</section>"""
    return layout("/bag", "Enquiry bag · Blush Tiny Blossoms", "The looks you would like to enquire about.", body, noindex=True)


def notfound():
    body = f"""<section class="section lost"><div class="wrap cta-band">
  <span style="color:var(--rose)">{BLOSSOM.replace('class="blossom"', 'class="blossom" style="width:34px;height:34px"')}</span>
  <span class="eyebrow">Page not found</span>
  <h1 style="font-size:clamp(2.4rem,6vw,4.4rem)">This path leads <em>out of the garden</em></h1>
  <div class="hero-cta"><a class="btn" href="/collection">View the collection</a><a class="btn ghost" href="/">Back home</a></div>
</div></section>"""
    return layout("/404", "Page not found · Blush Tiny Blossoms", "Page not found.", body, noindex=True)


def images():
    out = DIST / "img"; out.mkdir(parents=True)
    for l in LOOKS:
        for name in l["gallery"]:
            im = Image.open(src_img(name)).convert("RGB")
            DIMS[name] = (960, round(im.height * 960 / im.width))
            for w in (480, 960, 1600):
                if w == 1600 and im.width < 1200: continue
                im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(out / f"{name}-{w}.webp", "WEBP", quality={480: 74, 960: 78, 1600: 80}[w], method=6)
            if name != l["id"]: continue
            # social share image, 1200x630, cropped around the look's focal point
            fy = float(l["pos"].split()[1].rstrip("%")) / 100
            s = 1200 / im.width; r = im.resize((1200, round(im.height * s)), Image.LANCZOS)
            top = max(0, min(r.height - 630, round((r.height - 630) * fy)))
            r.crop((0, top, 1200, top + 630)).save(out / f"{l['id']}-og.jpg", "JPEG", quality=82, optimize=True, progressive=True)
    # Logo: src/img-orig/logo.png (header: BLUSH + tiny blossoms), logo-full.png (footer, with the heart), logo-icon.png (the flower: favicon and phone icon). All transparent.
    logo = Image.open(SRC / "img-orig" / "logo.png").convert("RGBA")
    logo = logo.resize((728, round(logo.height * 728 / logo.width)), Image.LANCZOS)
    logo.save(out / "logo.png", optimize=True)
    DIMS["logo"] = logo.size
    full = Image.open(SRC / "img-orig" / "logo-full.png").convert("RGBA")
    full = full.resize((560, round(full.height * 560 / full.width)), Image.LANCZOS); full.save(out / "logo-full.png", optimize=True)
    DIMS["logo-full"] = full.size
    icon = Image.open(SRC / "img-orig" / "logo-icon.png").convert("RGBA")
    def tile(n, pad):
        t = Image.new("RGBA", (n, n), "#FFFAF7"); m = icon.resize((n - 2 * pad, n - 2 * pad), Image.LANCZOS); t.alpha_composite(m, (pad, pad)); return t
    tile(180, 30).convert("RGB").save(DIST / "apple-touch-icon.png", optimize=True)
    tile(64, 4).save(DIST / "favicon.png", optimize=True)


def relative(page, prefix):
    """Turn root-absolute links (/collection, /img/x.webp) into relative ones, so the site works both on the
    custom domain and under username.github.io/repo/. The 404 page keeps absolute links (it can be served at any depth)."""
    page = re.sub(r'(href|src)="/([^"/][^"]*|)"', lambda m: f'{m[1]}="{prefix}{m[2]}"' if (prefix or m[2]) else f'{m[1]}="./"', page)
    return re.sub(r'srcset="([^"]*)"', lambda m: 'srcset="' + m[1].replace("/img/", prefix + "img/") + '"', page)


def fonts():
    """Fonts are self-hosted from src/fonts/ (both open source, SIL OFL): Fraunces for headings, a free soft serif
    close to Larken, and Jost for text. To switch to Larken later, add its .woff2 files and change the two
    Fraunces lines below plus --display in src/base.css."""
    (DIST / "fonts").mkdir(exist_ok=True)
    for f in (SRC / "fonts").iterdir(): shutil.copy(f, DIST / "fonts" / f.name)
    face = '@font-face{{font-family:"{}";src:url("../fonts/{}") format("woff2");font-weight:{};font-style:{};font-display:swap}}\n'
    return (face.format("Fraunces", "fraunces-latin-full-normal.woff2", "100 900", "normal") +
            face.format("Fraunces", "fraunces-latin-full-italic.woff2", "100 900", "italic") +
            face.format("Jost", "jost-latin-wght-normal.woff2", "100 900", "normal"))


def main():
    global VER
    DIST.mkdir(exist_ok=True)
    for c in DIST.iterdir():      # empty dist/ but keep the folder itself, so a running preview server survives a rebuild
        shutil.rmtree(c) if c.is_dir() else c.unlink()
    images()
    css = fonts() + "\n".join((SRC / f).read_text() for f in ("base.css", "extra.css", "pages.css"))
    js = (SRC / "site.js").read_text()
    data = {"shop": {k: SHOP[k] for k in ("instagram", "whatsapp", "currency", "mode", "checkoutUrl")},
            "looks": {l["id"]: {k: l.get(k) for k in ("id", "name", "variant", "priceBySize", "mrpBySize", "sizes", "soldout", "pos", "gallery")} for l in LOOKS}}
    data_js = "window.BLUSH = " + json.dumps(data, ensure_ascii=False) + ";\n"
    VER = hashlib.sha1((css + js + data_js).encode()).hexdigest()[:8]
    (DIST / "assets").mkdir()
    (DIST / "assets/site.css").write_text(css)
    (DIST / "assets/site.js").write_text(js)
    (DIST / "assets/data.js").write_text(data_js)
    pages = {"index.html": home(), "collection.html": collection(), "our-story.html": story(), "size-care.html": size_care(),
             "faq.html": faq_page(), "terms.html": terms_page(),
             "contact.html": contact(), "bag.html": bag(), "404.html": notfound()}
    (DIST / "looks").mkdir()
    for i, l in enumerate(LOOKS):
        pages[f"looks/{l['id']}.html"] = look(l, LOOKS[i - 1], LOOKS[(i + 1) % len(LOOKS)])
    for p, h in pages.items():
        (DIST / p).write_text(h if p == "404.html" else relative(h, "../" * p.count("/")))
    urls = ["/", "/collection", "/our-story", "/size-care", "/faq", "/terms", "/contact"] + [f"/looks/{l['id']}" for l in LOOKS]
    (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
                                      "".join(f"  <url><loc>{SHOP['domain']}{'' if u == '/' else u}</loc></url>\n" for u in urls) + "</urlset>\n")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SHOP['domain']}/sitemap.xml\n")
    (DIST / "CNAME").write_text(SHOP["domain"].split("//")[1] + "\n")   # custom domain for GitHub Pages
    (DIST / ".nojekyll").write_text("")
    total = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    print(f"built {len(pages)} pages, {total/1e6:.2f} MB, version {VER}")


if __name__ == "__main__":
    main()
