#!/usr/bin/env python3
"""Blush Tiny Blossoms — static site builder.  Run:  python3 build.py   →  writes ./dist

Everything a non-developer needs to change lives in the SETTINGS and LOOKS blocks below.
"""
import hashlib, html, json, shutil
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent
SRC, DIST = ROOT / "src", ROOT / "dist"

# ───────── SETTINGS: edit these ─────────
SHOP = {
    "name": "Blush Tiny Blossoms",
    "domain": "https://blushtinyblossoms.co.in",
    "instagram": "blushtinyblossoms",
    "whatsapp": "",          # e.g. "919812345678" (country code, no +). Empty hides every WhatsApp button.
    "currency": "₹",
    "mode": "enquiry",       # "enquiry" now. Switch to "store" once prices and checkoutUrl are set.
    "checkoutUrl": "",       # payment / checkout page, used only in "store" mode
}
GIRL_SIZES = ["2–3Y", "4–5Y", "6–8Y", "9–12Y", "13–16Y"]
BOY_SIZES = []               # empty = "Sizes on request"

# price: a number (e.g. 4500) shows the price; None shows "Price on request".
LOOKS = [
    dict(id="lavender-meadow", name="Lavender Meadow", sil="Sleeveless gingham kurta + tiered sharara", pal="Lavender / Ecru / Zari gold", cat=["sharara"], price=None, pos="50% 20%",
         fabric="Hand-loomed cotton gingham, gold gota edging", detail="Soft lavender checks layered with oversized wildflower bouquets. Sleeveless A-line kurta with tiered sharara, finished with fine kinari gota.", styling="Bare feet on grass, tiny jhumkis, braided hair."),
    dict(id="blush-tropica", name="Blush Tropica", sil="Peplum strappy top + tiered sharara", pal="Blush / Fern green / Cream", cat=["peplum", "sharara"], price=None,
         fabric="Blush pink gingham, tropical botanical print, cotton voile lining", detail="Signature strappy peplum with gathered hem, paired with a three-tier sharara. Hand-printed monstera and hibiscus in sage and rose.", styling="For a poolside mehendi. Add pearl flats."),
    dict(id="nilgiri", name="Nilgiri", sil="Full-sleeve kurta pant with gota", pal="Teal / Bubblegum / Mustard", cat=["kurta"], price=None,
         fabric="Teal cotton, hand-block tropical florals, pink triangle gota", detail="A quiet statement. Full sleeves, straight kurta with contrast pyjama. Inverted pink gota triangles at the hem and a tropical vine print at the border.", styling="Brother-sister twinning ready."),
    dict(id="daffodil-picnic", name="Daffodil Picnic", sil="Ruffle-sleeve peplum + wide palazzo", pal="Peony / Daffodil / Leaf", cat=["peplum"], price=None,
         fabric="Pink gingham, ruffle cap sleeves, daffodil border print", detail="Frill-sleeve peplum that flares like a tea rose. Wide palazzo with a hand-painted daffodil garden running along the hem.", styling="Birthday garden party. Mini potli in ivory."),
    dict(id="gulab-dust", name="Gulab Dust", sil="Embroidered kurta sharara set", pal="Dusty rose / Ivory / Sage", cat=["sharara"], price=None,
         fabric="Dusty rose handloom, mirror and resham floral embroidery", detail="Our most heirloom piece. Faded rose base with ivory and sage resham buttis, accented with tiny mirrors and French knots."),
    dict(id="rosewood-zari", name="Rosewood Zari", sil="Long-sleeve kurta sharara with sequin neckline", pal="Rosewood / Antique gold", cat=["sharara"], price=None,
         fabric="Rosewood pink cotton, gold sequin butti, zari yoke", detail="A longer silhouette with full sleeves. Deep neckline densely embroidered in gold sequin, with zari booti scattered across the sharara."),
    dict(id="haldi-orchard", name="Haldi Orchard", sil="Tie-up peplum + booti sharara", pal="Mustard / Marigold / Ecru", cat=["peplum", "sharara"], price=None,
         fabric="Mustard yellow cotton, tie-up yoke, hand-embroidered booti", detail="Front tie-up peplum with heavy yoke embroidery and tiny tassels. Sharara covered in all-over miniature floral buttis. Sunlit and festive.", styling="Haldi or Basant. Keep accessories minimal."),
    dict(id="lime-bahaar", name="Lime Bahaar", sil="Yoke-embroidered kurta sharara", pal="Chartreuse / Gulabi / Lime leaf", cat=["sharara"], price=None,
         fabric="Lime chartreuse cotton, pink gota and yoke embroidery", detail="Unexpected and joyful. Chartreuse kurta with a dense floral yoke and contrast pink gota at the tiered sharara seams. A favourite for photos."),
    dict(id="colorblock-bagh", name="Colorblock Bagh", sil="Gingham + ivory embroidered top & skirt", pal="Pink / Chikankari ivory / Garden green", cat=["coord"], price=None,
         fabric="Pink gingham, ivory chikankari embroidery, cotton skirt", detail="Playful colorblock. Pink gingham bodice with an ivory embroidered yoke and a full gathered skirt in ivory with gingham facing. Festive but light."),
    dict(id="colorblock-bagh-sunshine", name="Colorblock Bagh", variant="Sunshine", sil="Gingham + botanical panel top & skirt", pal="Sunshine / Teal / Ivory", cat=["coord"], price=None,
         fabric="Yellow gingham and teal botanical print cotton, lace trim", detail="The same garden colorblock in sunshine yellow. Gingham and teal botanical panels on the top and gathered skirt, finished with a soft lace hem."),
    dict(id="mogra-lehenga", name="Mogra Lehenga", sil="Halter choli + gathered lehenga", pal="Mint / Sequin / Blush", cat=["lehenga"], price=None, pos="50% 30%",
         fabric="Mint organza and cotton, sequin handwork", detail="Halter choli with delicate sitara work and an airy gathered lehenga."),
    dict(id="bagh-bandi", name="Bagh Bandi Set", sil="Kurta pyjama + botanical bandi jacket", pal="Sage / Rose / Fern", cat=["boys"], price=None, boys=True,
         fabric="Sage cotton kurta and pyjama, rose botanical print jacket", detail="For little brothers. A relaxed sage kurta and pyjama under a rose bandi printed with garden botanicals."),
]
FILTERS = [("all", "All looks", None), ("sharara", "Sharara sets", "lavender-meadow"), ("peplum", "Peplum sets", "daffodil-picnic"), ("kurta", "Kurta sets", "nilgiri"),
           ("coord", "Skirt co-ords", "colorblock-bagh"), ("lehenga", "Lehengas", "mogra-lehenga"), ("boys", "Boys", "bagh-bandi")]
FEATURED = ["lavender-meadow", "daffodil-picnic", "haldi-orchard", "colorblock-bagh"]
INSTA = ["blush-tropica", "lime-bahaar", "colorblock-bagh", "haldi-orchard", "daffodil-picnic", "lavender-meadow"]
# ───────── end of settings ─────────

e = html.escape
BY_ID = {l["id"]: l for l in LOOKS}
for l in LOOKS:
    l.setdefault("pos", "50% 35%")
    l["sizes"] = BOY_SIZES if l.get("boys") else GIRL_SIZES
IG = f"https://www.instagram.com/{SHOP['instagram']}/"
DM = f"https://ig.me/m/{SHOP['instagram']}"
DIMS = {}


def full(l): return l["name"] + (f" · {l['variant']}" if l.get("variant") else "")
def price(l): return f"{SHOP['currency']}{l['price']:,}" if l["price"] else "Price on request"
def title_html(l): return e(l["name"]) + (f' <em style="color:var(--ink-soft)">{e(l["variant"])}</em>' if l.get("variant") else "")


BLOSSOM = '<svg class="blossom" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="12" cy="5.5" r="3.4"/><circle cx="18.2" cy="10" r="3.4"/><circle cx="15.8" cy="17.2" r="3.4"/><circle cx="8.2" cy="17.2" r="3.4"/><circle cx="5.8" cy="10" r="3.4"/></svg>'
IG_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4.2"/><circle cx="17.4" cy="6.6" r=".9" fill="currentColor" stroke="none"/></svg>'
BAG_ICON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M5 8h14l-1 12H6L5 8z"/><path d="M9 8V6.5a3 3 0 0 1 6 0V8"/></svg>'
RULE = f'<div class="rule" aria-hidden="true" style="color:var(--rose)">{BLOSSOM}</div>'


def img(name, alt, sizes="(max-width:620px) 50vw, (max-width:1000px) 33vw, 25vw", pos=None, eager=False):
    w, h = DIMS[name]
    style = f' style="object-position:{pos}"' if pos else ""
    load = ' fetchpriority="high"' if eager else ' loading="lazy" decoding="async"'
    return (f'<img src="/img/{name}-960.webp" srcset="/img/{name}-480.webp 480w, /img/{name}-960.webp 960w" sizes="{sizes}" '
            f'width="{w}" height="{h}" alt="{e(alt)}"{style}{load}>')


def card(l, n=None):
    return (f'<a class="card" href="/looks/{l["id"]}" data-cat="{" ".join(l["cat"])}">'
            f'<div class="arch">{img(l["id"], full(l) + ": " + l["sil"], pos=l["pos"])}</div>'
            f'<div><h3>{title_html(l)}</h3>'
            f'<p class="sil">{e(l["sil"])}</p><p class="price">{price(l)}</p></div>'
            f'<span class="more">View look</span></a>')


NAV = [("/collection", "Collection"), ("/our-story", "Our Story"), ("/size-care", "Size &amp; Care"), ("/contact", "Contact")]


def layout(path, title, desc, body, og="blush-tropica", active=None, jsonld=None, noindex=False):
    url = SHOP["domain"] + ("" if path == "/" else path)
    links = "".join(f'<a href="{h}"{" aria-current=page" if h == active else ""}>{t}</a>' for h, t in NAV)
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    robots = '<meta name="robots" content="noindex">' if noindex else f'<link rel="canonical" href="{url}">'
    return f"""<!doctype html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{robots}
<meta name="theme-color" content="#FBF3F2">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SHOP['name']}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SHOP['domain']}/img/{og}-og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300;1,400&family=Jost:wght@300;400;500&display=swap">
<link rel="stylesheet" href="/assets/site.css?v={VER}">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="announce">Festive ’26 &nbsp;·&nbsp; The English Garden Edit &nbsp;·&nbsp; Limited pieces, made in India</div>
<header class="site-head">
  <div class="wrap">
    <button class="menu-btn" type="button" aria-label="Menu" aria-expanded="false" aria-controls="menu"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" aria-hidden="true"><path d="M3 7h18M3 12h18M3 17h18"/></svg></button>
    <nav class="nav left" id="menu" aria-label="Primary">{links}<a class="only-mobile" href="{IG}" target="_blank" rel="noopener">Instagram</a></nav>
    <a class="brand" href="/" aria-label="{SHOP['name']}, home"><img src="/img/logo.png" alt="Blush" width="728" height="203"><span>tiny blossoms</span></a>
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
        <a class="brand" href="/"><img src="/img/logo.png" alt="Blush" width="728" height="203" loading="lazy"><span>tiny blossoms</span></a>
        <p>Festive wear for little ones, made in limited pieces at our Shahpur Jat atelier, New Delhi.</p>
      </div>
      <div>
        <h4>Explore</h4>
        <ul><li><a href="/collection">The collection</a></li><li><a href="/our-story">Our story</a></li><li><a href="/size-care">Size &amp; care</a></li><li><a href="/bag">Enquiry bag</a></li></ul>
      </div>
      <div>
        <h4>Talk to us</h4>
        <ul>
          <li><a href="/contact">Send an enquiry</a></li>
          <li><a href="{DM}" target="_blank" rel="noopener">Message on Instagram</a></li>
          <li data-wa hidden><a href="#" target="_blank" rel="noopener">WhatsApp us</a></li>
          <li><a href="{IG}" target="_blank" rel="noopener">@{SHOP['instagram']}</a></li>
        </ul>
      </div>
    </div>
    <div class="legal"><span>© 2026 {SHOP['name']}</span><span>Made in India</span></div>
  </div>
</footer>
<script src="/assets/data.js?v={VER}"></script>
<script src="/assets/site.js?v={VER}"></script>
</body>
</html>
"""


STEPS = """<div class="steps">
      <div class="step"><h3>Choose a look</h3><p>Open any look to see its fabric, detailing and the sizes it comes in.</p></div>
      <div class="step"><h3>Message us</h3><p>Add looks to your enquiry bag, or send the look name and your child’s age on Instagram. We reply with price and availability.</p></div>
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


def size_chips(): return "".join(f"<span>{s}</span>" for s in GIRL_SIZES)


def home():
    hero_sizes = "(max-width:820px) 60vw, 30vw"
    body = f"""<section class="hero">
  <div class="wrap">
    <div class="hero-copy">
      <span class="eyebrow">Kids Festive ’26 · Ages 2 to 16</span>
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
        <a class="arch a3" href="/looks/mogra-lehenga">{img("mogra-lehenga", "Toddler in the mint Mogra Lehenga", hero_sizes, pos="50% 30%", eager=True)}</a>
      </div>
    </div>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap">
    {RULE}
    <div class="sec-head" style="margin-top:clamp(40px,6vw,72px)">
      <span class="eyebrow">The English Garden Edit</span>
      <h2>Twelve looks, <em>one garden</em></h2>
      <p>A first look at the edit. Open any piece for fabric, detail and sizes.</p>
    </div>
    <div class="grid">{"".join(card(BY_ID[i]) for i in FEATURED)}</div>
    <p class="center mt"><a class="btn ghost" href="/collection">See all twelve looks</a></p>
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
      <p>Nilgiri carries its teal tropical print across a relaxed kurta and pyjama, and the Bagh Bandi Set pairs a sage kurta with a rose botanical jacket. Dress them from the same garden without matching them exactly.</p>
      <a class="btn ghost" href="/collection?show=boys">See the boys’ look</a>
    </div>
    <div class="twin-art">
      <a class="arch" href="/looks/nilgiri">{img("nilgiri", "Girl in the teal Nilgiri kurta and pant", "(max-width:820px) 45vw, 25vw")}</a>
      <a class="arch" href="/looks/bagh-bandi">{img("bagh-bandi", "Boy in a sage kurta pyjama with rose botanical bandi jacket", "(max-width:820px) 45vw, 25vw")}</a>
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
        <h2>Kids to teen, <em style="color:#F0B4CC">one relaxed fit</em></h2>
        <p style="margin-top:22px"><a class="btn" style="background:#FFF6F7;color:var(--ink);border-color:#FFF6F7" href="/size-care">Size &amp; care guide</a></p>
      </div>
      <dl>
        <div><dt>Sizes</dt><dd><div class="sizes">{size_chips()}</div>Relaxed fit with side-seam pockets in the shararas. The tiered volume is scaled for teen lengths.</dd></div>
        <div><dt>Fabric</dt><dd>100% cotton bases with gota, sequin and resham handwork.</dd></div>
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
          "description": "Festive wear for children aged 2 to 16, made in limited pieces in New Delhi."}
    return layout("/", "Blush Tiny Blossoms · Kids’ festive wear, made in India",
                  "Festive wear for little ones aged 2 to 16. Hand-block florals, gingham and gota work, made in limited pieces at our Shahpur Jat atelier, New Delhi.", body, jsonld=ld)


def collection():
    filt = "".join(
        f'<button class="filter" type="button" data-key="{k}" aria-pressed="{"true" if k == "all" else "false"}">'
        f'<div class="thumb {"" if im else "all"}">{img(im, "", "104px", pos="50% 25%") if im else BLOSSOM}</div><span>{lab}</span></button>'
        for k, lab, im in FILTERS)
    body = f"""<section class="page-head">
  <div class="wrap">
    <span class="eyebrow">The English Garden Edit · Festive ’26</span>
    <h1>Twelve looks, <em>one garden</em></h1>
    <p class="lede">Open a look for fabric, detail and sizes, then add it to your enquiry bag.</p>
  </div>
</section>
<section class="section" style="padding-top:0">
  <div class="wrap">
    <div class="filters" id="filters" role="group" aria-label="Filter looks by silhouette">{filt}</div>
    <div class="grid" id="grid">{"".join(card(l) for l in LOOKS)}</div>
  </div>
</section>"""
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": "The English Garden Edit",
          "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{SHOP['domain']}/looks/{l['id']}", "name": full(l)} for i, l in enumerate(LOOKS)]}
    return layout("/collection", "The collection · Blush Tiny Blossoms",
                  "Twelve festive looks for children: tiered shararas, peplum sets, kurta sets, skirt co-ords and a lehenga, in gingham, hand-block florals and gota.", body, active="/collection", jsonld=ld)


def look(l, prev, nxt):
    sizes = l["sizes"]
    size_html = ("".join(f'<button type="button" aria-pressed="false">{s}</button>' for s in sizes) if sizes
                 else '<span class="hint">Sizes on request. Tell us his age and we will guide you.</span>')
    styling = f'<dt>Styling</dt><dd class="it">{e(l["styling"])}</dd>' if l.get("styling") else ""
    related = [x for x in LOOKS if x["id"] != l["id"] and set(x["cat"]) & set(l["cat"])]
    related = (related + [x for x in LOOKS if x["id"] != l["id"] and x not in related])[:4]
    body = f"""<section class="look" data-look="{l['id']}">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a><span>/</span><a href="/collection">Collection</a><span>/</span><span>{e(full(l))}</span></nav>
    <div class="look-art"><div class="arch">{img(l["id"], full(l) + ": " + l["sil"], "(max-width:820px) 92vw, 46vw", pos=l["pos"], eager=True)}</div></div>
    <div class="look-body">
      <span class="eyebrow">{e(l["pal"])}</span>
      <div><h1>{title_html(l)}</h1><p class="sil" style="margin-top:10px">{e(l["sil"])}</p></div>
      <p class="price">{price(l)}</p>
      <p class="desc">{e(l["detail"])}</p>
      <dl class="spec"><dt>Fabric</dt><dd>{e(l["fabric"])}</dd>{styling}<dt>Care</dt><dd>Dry-clean only</dd></dl>
      <div>
        <span class="field-label">{"Choose a size" if sizes else "Size"} · <a href="/size-care">Size guide</a></span>
        <div class="sizepick" id="look-sizes">{size_html}</div>
      </div>
      <div class="dlg-cta">
        <button class="btn" type="button" id="look-add">Add to enquiry bag</button>
        <a class="btn ghost" id="look-wa" href="#" target="_blank" rel="noopener" hidden>WhatsApp</a>
      </div>
      <p class="added" id="look-added" role="status"></p>
      <div>
        <span class="field-label">Or message us directly</span>
        <div class="msg" id="look-msg"></div>
      </div>
      <div class="dlg-cta">
        <button class="btn ghost" type="button" id="look-copy" data-label="Copy message">Copy message</button>
        <a class="btn ghost" href="{DM}" target="_blank" rel="noopener">Open Instagram chat</a>
      </div>
      <p class="hint">Copy the message, then paste it in our Instagram chat. We reply with price and availability.</p>
      <nav class="pager" aria-label="More looks">
        <a href="/looks/{prev['id']}"><span>Previous</span><b>{e(full(prev))}</b></a>
        <a href="/looks/{nxt['id']}"><span>Next</span><b>{e(full(nxt))}</b></a>
      </nav>
    </div>
  </div>
</section>
<section class="section band">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">From the same garden</span><h2>You may also <em>love</em></h2></div>
    <div class="grid">{"".join(card(x) for x in related)}</div>
  </div>
</section>"""
    ld = {"@context": "https://schema.org", "@type": "Product", "name": full(l), "description": l["detail"], "material": l["fabric"],
          "image": f"{SHOP['domain']}/img/{l['id']}-og.jpg", "brand": {"@type": "Brand", "name": SHOP["name"]}, "category": "Children's festive wear",
          "url": f"{SHOP['domain']}/looks/{l['id']}"}
    if l["price"]:
        ld["offers"] = {"@type": "Offer", "price": l["price"], "priceCurrency": "INR", "availability": "https://schema.org/InStock", "url": ld["url"]}
    return layout(f"/looks/{l['id']}", f"{full(l)} · {l['sil']} · Blush Tiny Blossoms", f"{l['detail']} {l['fabric']}.", body, og=l["id"], active="/collection", jsonld=ld)


def story():
    body = f"""<section class="page-head">
  <div class="wrap">
    <span class="eyebrow">Our story</span>
    <h1>Festive wear that lets little ones <em>be little</em></h1>
    <p class="lede">Clothes for running across lawns, spinning until dizzy and falling asleep in the car on the way home.</p>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap split" style="align-items:center">
    <div class="duo">
      <div class="arch">{img("gulab-dust", "Girl in the Gulab Dust embroidered kurta sharara", "(max-width:820px) 45vw, 24vw")}</div>
      <div class="arch">{img("lime-bahaar", "Girl in the chartreuse Lime Bahaar kurta sharara", "(max-width:820px) 45vw, 24vw")}</div>
    </div>
    <div class="story-copy">
      <span class="eyebrow">The atelier</span>
      <h2>Made in small numbers, <em>in Shahpur Jat</em></h2>
      <p class="body">Blush Tiny Blossoms makes festive wear for children aged two to sixteen. Every piece is cut and finished at our atelier in Shahpur Jat, New Delhi, in limited numbers, so each look stays a little rare.</p>
      <p class="body">We start with soft cotton, because a child who is comfortable is a child who is happy. Then come the things that make it festive: hand-block florals, fine kinari gota, mirror work and resham embroidery.</p>
    </div>
  </div>
</section>

<section class="section band">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">What we care about</span><h2>Three things, <em>every piece</em></h2></div>
    <div class="values">
      <div class="value" style="color:var(--rose)">{BLOSSOM}<h3 style="color:var(--ink)">Soft first</h3><p>100% cotton bases that sit gently on young skin, through a long evening of celebrations.</p></div>
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
                  "Blush Tiny Blossoms makes festive wear for children aged 2 to 16 in soft cotton, with hand-block florals and gota work, at our atelier in Shahpur Jat, New Delhi.", body, og="rosewood-zari", active="/our-story")


FAQ = [
    ("How do I order?", 'Choose a look and add it to your <a href="/bag">enquiry bag</a>, or message us on Instagram with the look name and your child’s age. We reply with price and availability, and confirm everything on chat before you pay.'),
    ("Why are prices on request?", "Each look is made in limited pieces. We share the price together with what is available in your size when you message us."),
    ("Which sizes do you make?", "Girls’ looks come in 2–3Y, 4–5Y, 6–8Y, 9–12Y and 13–16Y. For the boys’ Bagh Bandi Set, tell us his age and we will guide you."),
    ("My child is between sizes. What should I do?", "Send us height and chest measurements along with their age. We will suggest the size that fits best."),
    ("How long does delivery take?", "We confirm dispatch and delivery time on chat before you pay."),
    ("How do I care for the outfit?", "Dry-clean only. Professional dry-cleaning preserves the print and the embroidery."),
]


def faq_html():
    return '<div class="faq">' + "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in FAQ) + "</div>"


def size_care():
    rows = "".join(f"<tr><td>{s}</td><td>{a}</td></tr>" for s, a in zip(GIRL_SIZES, ["2 to 3 years", "4 to 5 years", "6 to 8 years", "9 to 12 years", "13 to 16 years"]))
    body = f"""<section class="page-head">
  <div class="wrap">
    <span class="eyebrow">Size &amp; care</span>
    <h1>Kids to teen, <em>one relaxed fit</em></h1>
    <p class="lede">Five sizes from two to sixteen years, cut with room to move and to grow.</p>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap split">
    <div>
      <h2>Our <em>sizes</em></h2>
      <table class="size-table">
        <thead><tr><th scope="col">Size</th><th scope="col">Age</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <p class="hint" style="margin-top:16px">Relaxed fit with side-seam pockets in the shararas. The tiered volume is scaled for teen lengths. Boys’ sizes are on request.</p>
    </div>
    <div>
      <h2>How to <em>measure</em></h2>
      <ol class="measure">
        <li><b>Height</b><span>Standing straight against a wall, without shoes, from the floor to the top of the head.</span></li>
        <li><b>Chest</b><span>Around the fullest part of the chest, under the arms, with the tape level and comfortably loose.</span></li>
        <li><b>Waist</b><span>Around the natural waist, where the sharara or pyjama will sit.</span></li>
      </ol>
      <p style="margin-top:24px;color:var(--ink-soft)">Send us these with your child’s age if you are between sizes, and we will guide you before you pay.</p>
      <p style="margin-top:22px"><a class="btn ghost" href="/contact">Ask about sizing</a></p>
    </div>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap">
    <div class="care" style="margin-top:0">
      <div>
        <span class="eyebrow">Fabric &amp; care</span>
        <h2>Looked after, <em style="color:#F0B4CC">it lasts</em></h2>
      </div>
      <dl>
        <div><dt>Fabric</dt><dd>100% cotton bases with gota, sequin and resham handwork.</dd></div>
        <div><dt>Care</dt><dd>Dry-clean only. Professional dry-cleaning preserves the print and embroidery.</dd></div>
        <div><dt>Fit</dt><dd>Relaxed through the body, with tiered volume in the shararas.</dd></div>
      </dl>
    </div>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Good to know</span><h2>Questions, <em>answered</em></h2></div>
    {faq_html()}
  </div>
</section>"""
    import re
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", a)}} for q, a in FAQ]}
    return layout("/size-care", "Size & care · Blush Tiny Blossoms",
                  "Sizes from 2–3Y to 13–16Y, how to measure your child, fabric and care for Blush Tiny Blossoms festive wear.", body, og="lavender-meadow", active="/size-care", jsonld=ld)


def contact():
    opts = '<option value="">The whole collection</option>' + "".join(f'<option value="{l["id"]}">{e(full(l))}</option>' for l in LOOKS)
    sz = '<option value="">Not sure yet</option>' + "".join(f"<option>{s}</option>" for s in GIRL_SIZES)
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
      <div class="way"><span class="eyebrow">Instagram</span><h3>Message us</h3><p>The quickest way to reach us. Send the look name and your child’s age.</p><a class="btn" href="{DM}" target="_blank" rel="noopener">Open Instagram chat</a></div>
      <div class="way" data-wa hidden><span class="eyebrow">WhatsApp</span><h3>Chat on WhatsApp</h3><p>Prefer WhatsApp? Send us a message and we will take it from there.</p><a class="btn ghost" href="#" target="_blank" rel="noopener">WhatsApp us</a></div>
      <div class="way"><span class="eyebrow">Atelier</span><h3>Shahpur Jat, New Delhi</h3><p>Where every piece is cut, embroidered and finished, in limited numbers.</p><a class="btn ghost" href="/our-story">Our story</a></div>
    </div>
  </div>
</section>

<section class="section band">
  <div class="wrap">
    <div class="sec-head"><span class="eyebrow">Send an enquiry</span><h2>Tell us what you <em>need</em></h2><p>Fill this in and we will write the message for you. Copy it, then paste it in our Instagram chat.</p></div>
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
          <button class="btn" type="button" id="enq-copy" data-label="Copy message">Copy message</button>
          <a class="btn ghost" href="{DM}" target="_blank" rel="noopener">Open Instagram chat</a>
          <a class="btn ghost" id="enq-wa" data-msg="1" href="#" target="_blank" rel="noopener" hidden>Send on WhatsApp</a>
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
    <p class="lede">Send everything in one message. We reply with price and availability.</p>
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
        im = Image.open(SRC / "img-orig" / f"{l['id']}.jpg").convert("RGB")
        DIMS[l["id"]] = (960, round(im.height * 960 / im.width))
        for w in (480, 960):
            im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(out / f"{l['id']}-{w}.webp", "WEBP", quality=78 if w == 960 else 74, method=6)
        # social share image, 1200x630, cropped around the look's focal point
        fy = float(l["pos"].split()[1].rstrip("%")) / 100
        s = 1200 / im.width; r = im.resize((1200, round(im.height * s)), Image.LANCZOS)
        top = max(0, min(r.height - 630, round((r.height - 630) * fy)))
        r.crop((0, top, 1200, top + 630)).save(out / f"{l['id']}-og.jpg", "JPEG", quality=82, optimize=True, progressive=True)
    logo = Image.open(SRC / "img-orig" / "logo.png").convert("RGBA").resize((728, 203), Image.LANCZOS)
    logo.save(out / "logo.png", optimize=True)
    tile = Image.new("RGB", (180, 180), "#FBF3F2")
    mark = logo.resize((150, round(203 * 150 / 728)), Image.LANCZOS)
    tile.paste(mark, (15, (180 - mark.height) // 2), mark)
    tile.save(DIST / "apple-touch-icon.png", optimize=True)


def main():
    global VER
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir()
    images()
    css = (SRC / "base.css").read_text() + "\n" + (SRC / "extra.css").read_text()
    js = (SRC / "site.js").read_text()
    data = {"shop": {k: SHOP[k] for k in ("instagram", "whatsapp", "currency", "mode", "checkoutUrl")},
            "looks": {l["id"]: {k: l.get(k) for k in ("id", "name", "variant", "price", "sizes", "pos")} for l in LOOKS}}
    data_js = "window.BLUSH = " + json.dumps(data, ensure_ascii=False) + ";\n"
    VER = hashlib.sha1((css + js + data_js).encode()).hexdigest()[:8]
    (DIST / "assets").mkdir()
    (DIST / "assets/site.css").write_text(css)
    (DIST / "assets/site.js").write_text(js)
    (DIST / "assets/data.js").write_text(data_js)
    pages = {"index.html": home(), "collection.html": collection(), "our-story.html": story(), "size-care.html": size_care(),
             "contact.html": contact(), "bag.html": bag(), "404.html": notfound()}
    (DIST / "looks").mkdir()
    for i, l in enumerate(LOOKS):
        pages[f"looks/{l['id']}.html"] = look(l, LOOKS[i - 1], LOOKS[(i + 1) % len(LOOKS)])
    for p, h in pages.items():
        (DIST / p).write_text(h)
    (DIST / "favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect width="24" height="24" rx="6" fill="#FBF3F2"/><g fill="#DC86AA" transform="translate(2.4 2.6) scale(.8)"><circle cx="12" cy="5.5" r="3.4"/><circle cx="18.2" cy="10" r="3.4"/><circle cx="15.8" cy="17.2" r="3.4"/><circle cx="8.2" cy="17.2" r="3.4"/><circle cx="5.8" cy="10" r="3.4"/></g><circle cx="12" cy="11.7" r="1.9" fill="#FBF3F2"/></svg>')
    urls = ["/", "/collection", "/our-story", "/size-care", "/contact"] + [f"/looks/{l['id']}" for l in LOOKS]
    (DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
                                      "".join(f"  <url><loc>{SHOP['domain']}{'' if u == '/' else u}</loc></url>\n" for u in urls) + "</urlset>\n")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SHOP['domain']}/sitemap.xml\n")
    (ROOT / "vercel.json").write_text(json.dumps({
        "outputDirectory": "dist", "cleanUrls": True, "trailingSlash": False,
        "headers": [{"source": "/img/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=2592000"}]},
                    {"source": "/assets/(.*)", "headers": [{"key": "Cache-Control", "value": "public, max-age=31536000, immutable"}]}]}, indent=2))
    total = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
    print(f"built {len(pages)} pages, {total/1e6:.2f} MB, version {VER}")


if __name__ == "__main__":
    main()
