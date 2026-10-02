# Blush Tiny Blossoms — website

Static site for blushtinyblossoms.co.in. No framework: `build.py` turns the settings and look data at the top of the file into the pages in `docs/`, which GitHub Pages serves.

## Change something

1. Edit the **SETTINGS** / **LOOKS** block at the top of `build.py` (prices, WhatsApp number, look names, sizes).
2. Run `python3 build.py` (needs Python 3 and `pip install pillow`).
3. Commit and push. GitHub Pages republishes within a minute or two of every push to `main`.

Preview locally with `python3 serve.py`, then open http://127.0.0.1:8123.

| Setting | Effect |
|---|---|
| `SHOP["whatsapp"]` | Country code + number, no `+`. Empty hides every WhatsApp button. |
| `LOOKS[..]["prices"]` | Five numbers, one per size band; `None` shows "Price on request". |
| `SHOP["mode"]`, `SHOP["checkoutUrl"]` | See below. |

## Add a new look (no limit)

1. Put the main photo in `src/img-orig/<id>.jpg` (for example `rose-garden.jpg`). Extra gallery photos: `<id>-2.jpg`, `<id>-3.jpg` … they appear as thumbnails and in the zoom view on the look page, and the second one shows when you hover a card.
2. Add a `dict(id="<id>", …)` to `LOOKS` in `build.py` (copy an existing one). Optional fields: `mrp` (sale price strike-through), `soldout` (sizes), `new=True` (tag).
3. `python3 build.py`, commit, push. The collection, filters, counts, sitemap, related looks and bag pick it up automatically. No heading mentions a fixed number of looks.

## Policies, FAQ, terms

`POLICY` in `build.py` holds every number used on `/faq`, `/terms` and the "Delivery & returns" panel on each look (free delivery threshold, dispatch time, exchange window…). `NOTICE` is the highlighted delivery note on look pages. `SHOP["hours"]`, `SHOP["email"]` show in the support box and footer. Size chart data is `SIZE_CHART` (from the "Size Chart" tab of the Google Sheet).

## Logo

`src/img-orig/logo.png` (horizontal lockup, transparent) is used in the header; `src/img-orig/logo-round.png` (round badge) in the footer, favicon and phone home-screen icon.

## Fonts

Both fonts are open source and hosted with the site from `src/fonts/` (no Google Fonts request): **Fraunces** for headings, a free soft serif close to Larken, and **Jost** for text. To use Larken itself later, add its licensed `.woff2` files to `src/fonts/` and change `fonts()` in `build.py` and `--display` in `src/base.css`.

## Prices and sizes

Prices come from the "Collection Pricing" tab of the BlushTinyBlossoms Google Sheet: five size bands per look, two sizes per band. In `build.py`, each look has `prices=[band1, band2, band3, band4, band5]`; `SIZES` lists the ten sizes. Cards show "From ₹…", the look page shows the price for the chosen size, and the bag adds up a total. `prices=None` shows "Price on request". The Our Story text comes from the "Story" tab.

## Layout

- `build.py` — data, page templates, image processing
- `src/base.css`, `src/extra.css`, `src/site.js` — styles and behaviour
- `src/img-orig/` — original photographs (the build makes 480px / 960px WebP and 1200×630 share images)
- `docs/` — generated site, published by GitHub Pages (Settings → Pages → Deploy from a branch → `main` / `docs`). Includes `CNAME` for the custom domain.

## Pages

`/` · `/collection` (filter with `?show=sharara|peplum|kurta|coord|lehenga|boys`) · `/looks/<id>` · `/our-story` · `/size-care` (size guide) · `/faq` · `/terms` · `/contact` (`?look=<id>` preselects) · `/bag` · 404

## From enquiry to online store

The site already behaves like a shop up to the point of payment: each look has its own page with a size picker, an "Add to enquiry bag" button, and a bag page with quantities. Today the bag ends in a composed order message for WhatsApp or Instagram.

To start selling online:

1. Prices are already in, so the bag shows a total. Choose how payment is taken (for example Razorpay, or moving the catalogue to Shopify) and set `SHOP["checkoutUrl"]`.
2. Set `SHOP["mode"] = "store"`. The bag then shows a Checkout button ahead of the enquiry buttons.

Not built yet, and needed before real checkout: passing the bag contents to the payment provider, stock per size, delivery charges, order confirmation emails, (shipping, returns, privacy and terms are now covered by `/faq` and `/terms`). The bag logic is isolated in the `Bag` object in `src/site.js` so it can be swapped for a real cart.
