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

`src/img-orig/logo.png` (the bird + BLUSH + tiny blossoms, transparent) is used in the header, `logo-full.png` in the footer, and `logo-icon.png` (the bird) for the favicon and phone home-screen icon.

## Online payments (Cashfree)

The site has a Checkout page (`/checkout`) and an order confirmation page (`/order`). They switch on when `SHOP["checkoutApi"]` in `build.py` holds the address of the checkout service. While it is empty the site stays in enquiry mode.

The checkout service is `worker/checkout-worker.js`, a Cloudflare Worker (free plan). It keeps the Cashfree secret key, prices every order from the live `/assets/catalog.json` (so prices can't be changed in the browser), adds delivery (free above `POLICY["free_above"]`), creates the Cashfree order and confirms payment.

Set up once:
1. Cloudflare → Workers & Pages → Create → Worker → name it `blush-checkout` → Deploy → Edit code → replace everything with `worker/checkout-worker.js` → Deploy.
2. Worker → Settings → Variables and Secrets: `CASHFREE_APP_ID` (text), `CASHFREE_SECRET` (Secret), `CASHFREE_ENV` = `sandbox`, `SITE_URL` = `https://blushtinyblossoms.co.in`.
3. Put the worker address (`https://blush-checkout.<you>.workers.dev`) in `SHOP["checkoutApi"]`, run `python3 build.py`, upload.
4. Cashfree → Developers → Whitelisting: add `blushtinyblossoms.co.in`.
5. Optional order emails: Cashfree → Developers → Webhooks → add `https://blush-checkout.<you>.workers.dev/webhook`; in the worker add `RESEND_API_KEY` (Secret, from resend.com) and `NOTIFY_EMAIL`.

Going live: swap in the production App ID and Secret, set `CASHFREE_ENV` = `production` in Cloudflare and `SHOP["cashfreeMode"]` = `"production"` in `build.py`, rebuild and upload. Every order also shows in the Cashfree dashboard with the address and items in its order tags.

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

## Welcome offer (first-order discount)

`welcomePct` in `build.py` switches on a first-visit pop-up (name, mobile, optional email) and a discount at checkout for the same mobile number or email, usable once. Sign-ups and their status are kept in the "Customers" tab of the BlushTinyBlossoms Google Sheet.

Set up once: paste `worker/customers-sheet.gs` into the Sheet's Apps Script and deploy it as a web app (steps are at the top of that file), then add `SHEET_API` and `SHEET_KEY` to the Cloudflare worker and deploy `worker/checkout-worker.js`. Without those two settings the pop-up cannot save and no discount is given. Set `welcomePct` to `0` to remove the pop-up.
