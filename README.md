# Blush Tiny Blossoms — website

Static site for blushtinyblossoms.co.in. No framework: `build.py` turns the settings and look data at the top of the file into the pages in `dist/`, which is what Vercel serves.

## Change something

1. Edit the **SETTINGS** / **LOOKS** block at the top of `build.py` (prices, WhatsApp number, look names, sizes).
2. Run `python3 build.py` (needs Python 3 and `pip install pillow`).
3. Commit and push. Vercel redeploys on every push to `main`.

Preview locally with `python3 serve.py`, then open http://127.0.0.1:8123.

| Setting | Effect |
|---|---|
| `SHOP["whatsapp"]` | Country code + number, no `+`. Empty hides every WhatsApp button. |
| `LOOKS[..]["price"]` | A number shows the price; `None` shows "Price on request". |
| `BOY_SIZES` | Empty shows "Sizes on request" on boys' looks. |
| `SHOP["mode"]`, `SHOP["checkoutUrl"]` | See below. |

## Layout

- `build.py` — data, page templates, image processing
- `src/base.css`, `src/extra.css`, `src/site.js` — styles and behaviour
- `src/img-orig/` — original photographs (the build makes 480px / 960px WebP and 1200×630 share images)
- `dist/` — generated site (committed, so Vercel needs no build step)
- `vercel.json` — generated; serves `dist/` with clean URLs

## Pages

`/` · `/collection` (filter with `?show=sharara|peplum|kurta|coord|lehenga|boys`) · `/looks/<id>` · `/our-story` · `/size-care` · `/contact` (`?look=<id>` preselects) · `/bag` · 404

## From enquiry to online store

The site already behaves like a shop up to the point of payment: each look has its own page with a size picker, an "Add to enquiry bag" button, and a bag page with quantities. Today the bag ends in a composed message for Instagram or WhatsApp.

To start selling online:

1. Fill in every `price` in `LOOKS`. The bag then shows a subtotal and look pages publish price data to Google.
2. Choose how payment is taken (for example Razorpay, or moving the catalogue to Shopify) and set `SHOP["checkoutUrl"]`.
3. Set `SHOP["mode"] = "store"`. The bag then shows a Checkout button ahead of the enquiry buttons.

Not built yet, and needed before real checkout: passing the bag contents to the payment provider, stock per size, delivery charges, order confirmation emails, and the policy pages a payment gateway asks for (shipping, returns, privacy, terms). The bag logic is isolated in the `Bag` object in `src/site.js` so it can be swapped for a real cart.
