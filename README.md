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

`/` · `/collection` (filter with `?show=sharara|peplum|kurta|coord|lehenga|boys`) · `/looks/<id>` · `/our-story` · `/size-care` · `/contact` (`?look=<id>` preselects) · `/bag` · 404

## From enquiry to online store

The site already behaves like a shop up to the point of payment: each look has its own page with a size picker, an "Add to enquiry bag" button, and a bag page with quantities. Today the bag ends in a composed order message for WhatsApp or Instagram.

To start selling online:

1. Prices are already in, so the bag shows a total. Choose how payment is taken (for example Razorpay, or moving the catalogue to Shopify) and set `SHOP["checkoutUrl"]`.
2. Set `SHOP["mode"] = "store"`. The bag then shows a Checkout button ahead of the enquiry buttons.

Not built yet, and needed before real checkout: passing the bag contents to the payment provider, stock per size, delivery charges, order confirmation emails, and the policy pages a payment gateway asks for (shipping, returns, privacy, terms). The bag logic is isolated in the `Bag` object in `src/site.js` so it can be swapped for a real cart.
