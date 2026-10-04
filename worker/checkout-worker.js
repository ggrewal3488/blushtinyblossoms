/*
 * Blush Tiny Blossoms: checkout service (Cloudflare Worker, free plan).
 *
 * Why it exists: the website is static, so it cannot keep the Cashfree secret key. This small service
 * creates each Cashfree order with the key, works out the price itself from the live catalogue
 * (so nobody can change a price in their browser), and confirms whether an order was paid.
 *
 * Endpoints
 *   POST /create-order   { items:[{id,size,qty}], customer:{name,phone,email,address1,address2,city,state,pin,note} }
 *                        → { order_id, payment_session_id, amount, mode }
 *   GET  /order-status?order_id=…  → { order_id, status, paid, amount, items, name }
 *   POST /webhook        Cashfree payment webhook (signature checked). Sends the order email if set up.
 *   POST /signup         { name, phone, email }  welcome-offer pop-up → saved to the Google Sheet → { ok, pct, used }
 *   POST /offer          { phone, email } → { eligible, pct }  (does this mobile / email have an unused welcome offer?)
 *
 * Settings (Cloudflare → Workers → this worker → Settings → Variables and Secrets)
 *   CASHFREE_APP_ID      App ID from Cashfree (Developers → API Keys)
 *   CASHFREE_SECRET      Secret Key from Cashfree  ← add as type "Secret"
 *   CASHFREE_ENV         "sandbox" while testing, "production" when live
 *   SITE_URL             https://blushtinyblossoms.co.in
 *   Welcome offer (optional; without these the pop-up cannot save and no discount is given):
 *     SHEET_API          the Google Apps Script web-app address (ends in /exec), see worker/customers-sheet.gs
 *     SHEET_KEY          the same secret phrase you typed into that script  ← add as type "Secret"
 *     WELCOME_PCT        discount percent, default 10 (keep it equal to welcomePct in build.py)
 *   Optional: ALLOWED_ORIGINS (extra comma-separated origins), CASHFREE_API_VERSION,
 *             RESEND_API_KEY + NOTIFY_EMAIL (+ EMAIL_FROM) to receive an email for every paid order.
 */

const API_VERSION = "2026-01-01";
const MAX_ITEMS = 20;
let catalogCache = null, catalogAt = 0;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const cors = corsHeaders(request, env);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
    try {
      if (url.pathname === "/create-order" && request.method === "POST") return json(await createOrder(request, env), 200, cors);
      if (url.pathname === "/order-status" && request.method === "GET") return json(await orderStatus(url.searchParams.get("order_id"), env, ctx), 200, cors);
      if (url.pathname === "/signup" && request.method === "POST") return json(await signup(request, env), 200, cors);
      if (url.pathname === "/offer" && request.method === "POST") return json(await offerCheck(request, env), 200, cors);
      if (url.pathname === "/webhook" && request.method === "POST") return await webhook(request, env, ctx);
      if (url.pathname === "/" || url.pathname === "/health") return json({ ok: true, mode: env.CASHFREE_ENV || "sandbox", configured: !!(env.CASHFREE_APP_ID && env.CASHFREE_SECRET), offer: offerOn(env) ? pct(env) : 0 }, 200, cors);
      return json({ error: "Not found" }, 404, cors);
    } catch (e) {
      const status = e.status || 500;
      if (!e.status) console.error(e && e.stack || e);
      return json({ error: e.status ? e.message : "Something went wrong. Please try again, or message us on WhatsApp." }, status, cors);
    }
  },
};

/* ── create an order ── */
async function createOrder(request, env) {
  need(env.CASHFREE_APP_ID && env.CASHFREE_SECRET && env.SITE_URL, "Checkout is not set up yet.", 503);
  let body;
  try { body = await request.json(); } catch { throw bad("Invalid request."); }
  const cat = await catalog(env);
  const lines = priceItems(body.items, cat);
  const c = cleanCustomer(body.customer);
  const subtotal = lines.reduce((n, l) => n + l.price * l.qty, 0);
  const shipping = subtotal >= cat.shipping.free_above ? 0 : cat.shipping.fee;
  // Welcome offer: only for a mobile / email that signed up in the pop-up and has not used it. Decided here, never in the browser.
  const offer = await offerFor(env, c.phone, c.email);
  const discount = offer.eligible ? Math.min(subtotal - 1, Math.round(subtotal * pct(env) / 100)) : 0;
  const amount = subtotal - discount + shipping;

  const orderId = "BTB-" + new Date().toISOString().slice(2, 10).replace(/-/g, "") + "-" + randomId(6);
  const itemsText = lines.map(l => `${l.qty}x ${l.name} ${l.size}`).join(" / ");
  const site = env.SITE_URL.replace(/\/$/, "");
  const payload = {
    order_id: orderId,
    order_amount: amount,
    order_currency: "INR",
    customer_details: {
      customer_id: "c" + c.phone,
      customer_phone: c.phone,
      customer_name: c.name,
      ...(c.email ? { customer_email: c.email } : {}),
    },
    order_meta: { return_url: `${site}/order?order_id={order_id}` },
    order_note: clip(safeText(`${itemsText}${shipping ? " plus delivery" : ""}`), 200),
    order_tags: compactTags({
      items: itemsText,
      subtotal: String(subtotal),
      delivery: String(shipping),
      discount: discount ? String(discount) : "",
      name: c.name,
      address: [c.address1, c.address2].filter(Boolean).join(", "),
      city: c.city,
      state: c.state,
      pin: c.pin,
      note: c.note,
    }),
  };
  const res = await cashfree(env, "POST", "/orders", payload);
  if (discount) await sheet(env, "reserve", { phone: c.phone, email: c.email, order_id: orderId });   // one live discounted order per customer
  return { order_id: res.order_id, payment_session_id: res.payment_session_id, amount, subtotal, shipping, discount, mode: mode(env) };
}

function priceItems(items, cat) {
  if (!Array.isArray(items) || !items.length) throw bad("Your bag is empty.");
  if (items.length > MAX_ITEMS) throw bad("Too many items in one order.");
  return items.map(i => {
    const look = cat.looks[String(i && i.id)];
    if (!look) throw bad("A piece in your bag is no longer available. Please refresh the page.");
    const size = String(i.size || "");
    if (!look.priceBySize) throw bad(`${look.name} can’t be bought online yet. Please message us on WhatsApp for it.`);
    const price = look.priceBySize[size];
    if (!price) throw bad(`${look.name}: please choose a size.`);
    if ((look.soldout || []).includes(size)) throw bad(`${look.name} in ${size} is sold out.`);
    const qty = Math.max(1, Math.min(9, parseInt(i.qty, 10) || 1));
    return { id: look.id, name: look.name + (look.variant ? " " + look.variant : ""), size, qty, price };
  });
}

function cleanCustomer(c) {
  c = c || {};
  const s = (v, max) => String(v == null ? "" : v).replace(/[\u0000-\u001f<>]/g, " ").replace(/\s+/g, " ").trim().slice(0, max);
  const out = {
    name: s(c.name, 80), phone: String(c.phone || "").replace(/\D/g, "").replace(/^(91|0)(?=\d{10}$)/, ""),
    email: s(c.email, 120), address1: s(c.address1, 160), address2: s(c.address2, 160),
    city: s(c.city, 60), state: s(c.state, 60), pin: String(c.pin || "").replace(/\D/g, ""), note: s(c.note, 200),
  };
  if (out.name.length < 2) throw bad("Please enter your name.");
  if (!/^[6-9]\d{9}$/.test(out.phone)) throw bad("Please enter a 10-digit mobile number.");
  if (out.email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(out.email)) throw bad("Please check your email address.");
  if (out.address1.length < 5) throw bad("Please enter your delivery address.");
  if (out.city.length < 2) throw bad("Please enter your city.");
  if (out.state.length < 2) throw bad("Please enter your state.");
  if (!/^[1-9]\d{5}$/.test(out.pin)) throw bad("Please enter a 6-digit PIN code.");
  return out;
}

/* ── check an order ── */
async function orderStatus(orderId, env, ctx) {
  need(env.CASHFREE_APP_ID && env.CASHFREE_SECRET, "Checkout is not set up yet.", 503);
  if (!/^[A-Za-z0-9_-]{3,45}$/.test(orderId || "")) throw bad("Unknown order.");
  const o = await cashfree(env, "GET", "/orders/" + encodeURIComponent(orderId));
  const tags = o.order_tags || {};
  if (o.order_status === "PAID" && Number(tags.discount) > 0 && ctx) ctx.waitUntil(redeem(o, env));
  return {
    order_id: o.order_id, status: o.order_status, paid: o.order_status === "PAID", amount: o.order_amount,
    items: tags.items || o.order_note || "", name: (o.customer_details && o.customer_details.customer_name) || tags.name || "",
  };
}

/* ── Cashfree webhook: verify signature, then email the order (optional) ── */
async function webhook(request, env, ctx) {
  const raw = await request.text();
  const ts = request.headers.get("x-webhook-timestamp") || "";
  const sig = request.headers.get("x-webhook-signature") || "";
  const expected = await hmacBase64(env.CASHFREE_SECRET || "", ts + raw);
  if (!sig || !timingSafeEqual(sig, expected)) return new Response("bad signature", { status: 401 });
  let evt; try { evt = JSON.parse(raw); } catch { return new Response("bad json", { status: 400 }); }
  const orderId = evt && evt.data && evt.data.order && evt.data.order.order_id;
  const paid = evt && evt.data && evt.data.payment && evt.data.payment.payment_status === "SUCCESS";
  if (orderId && paid) ctx.waitUntil((async () => {
    const o = await cashfree(env, "GET", "/orders/" + encodeURIComponent(orderId));
    if (o.order_status === "PAID" && Number((o.order_tags || {}).discount) > 0) await redeem(o, env);
  })().catch(e => console.error("redeem", e && e.message)));
  if (orderId && paid && env.RESEND_API_KEY && env.NOTIFY_EMAIL) ctx.waitUntil(notify(orderId, env));
  return new Response("ok");
}

async function notify(orderId, env) {
  const o = await cashfree(env, "GET", "/orders/" + encodeURIComponent(orderId));
  if (o.order_status !== "PAID") return;
  const t = o.order_tags || {}, cd = o.customer_details || {};
  const rows = [
    ["Order", o.order_id], ["Amount", "₹" + o.order_amount], ["Items", t.items || o.order_note],
    ["Subtotal", "₹" + (t.subtotal || "")], ["Welcome offer", t.discount ? "-₹" + t.discount : ""], ["Delivery", "₹" + (t.delivery || "0")],
    ["Name", cd.customer_name || t.name], ["Phone", cd.customer_phone], ["Email", cd.customer_email || t.email || ""],
    ["Address", [t.address, t.city, t.state, t.pin].filter(Boolean).join(", ")], ["Note", t.note || ""],
  ];
  const text = rows.map(([k, v]) => `${k}: ${v || "-"}`).join("\n");
  await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: "Bearer " + env.RESEND_API_KEY, "Content-Type": "application/json" },
    body: JSON.stringify({ from: env.EMAIL_FROM || "Blush Orders <onboarding@resend.dev>", to: [env.NOTIFY_EMAIL], subject: `New paid order ${o.order_id} · ₹${o.order_amount}`, text }),
  });
}

/* ── welcome offer (customers live in the Google Sheet, reached through a small Apps Script web app) ── */
const offerOn = env => !!(env.SHEET_API && env.SHEET_KEY);
const pct = env => Math.max(0, Math.min(50, parseInt(env.WELCOME_PCT, 10) || 10));
const normPhone = v => String(v || "").replace(/\D/g, "").replace(/^(91|0)(?=\d{10}$)/, "");
const normEmail = v => String(v || "").trim().toLowerCase().slice(0, 120);
const okPhone = p => /^[6-9]\d{9}$/.test(p), okEmail = m => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(m);

async function sheet(env, action, data) {
  if (!offerOn(env)) return null;
  try {
    const r = await fetch(env.SHEET_API, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ key: env.SHEET_KEY, action, ...data }), redirect: "follow" });
    const d = await r.json();
    if (!d || d.ok !== true) { console.error("sheet", action, JSON.stringify(d).slice(0, 300)); return null; }
    return d;
  } catch (e) { console.error("sheet", action, e && e.message); return null; }
}

async function signup(request, env) {
  need(offerOn(env), "This offer is not available right now.", 503);
  let b; try { b = await request.json(); } catch { throw bad("Invalid request."); }
  const name = String(b.name || "").replace(/[\u0000-\u001f<>]/g, " ").replace(/\s+/g, " ").trim().slice(0, 80);
  const phone = normPhone(b.phone), email = normEmail(b.email);
  if (name.length < 2) throw bad("Please enter your name.");
  if (!okPhone(phone)) throw bad("Please enter a 10-digit mobile number.");
  if (email && !okEmail(email)) throw bad("Please check your email address.");
  const d = await sheet(env, "signup", { name, phone, email, page: String(b.page || "").slice(0, 80) });
  need(d, "We could not save that just now. Please try again.", 502);
  return { ok: true, pct: pct(env), used: d.status === "used" };
}

async function offerCheck(request, env) {
  let b; try { b = await request.json(); } catch { throw bad("Invalid request."); }
  const o = await offerFor(env, normPhone(b.phone), normEmail(b.email), true);
  return { eligible: o.eligible, pct: o.eligible ? pct(env) : 0 };
}

/* Is there an unused welcome offer for this mobile / email? An offer with an order in progress is settled first:
   paid → used; unpaid → that order is closed so only one discounted order can ever be paid. */
async function offerFor(env, phone, email, peek) {
  if (!offerOn(env) || (!okPhone(phone) && !okEmail(email))) return { eligible: false };
  const d = await sheet(env, "check", { phone: okPhone(phone) ? phone : "", email: okEmail(email) ? email : "" });
  if (!d || d.status === "none" || d.status === "used") return { eligible: false };
  if (d.status === "pending" && d.order_id) {
    let o = null;
    try { o = await cashfree(env, "GET", "/orders/" + encodeURIComponent(d.order_id)); } catch (e) {}
    if (o && o.order_status === "PAID") { await redeem(o, env); return { eligible: false }; }
    if (peek) return { eligible: true };
    if (o && o.order_status === "ACTIVE") {
      try { await cashfree(env, "PATCH", "/orders/" + encodeURIComponent(d.order_id), { order_status: "TERMINATED" }); }
      catch (e) { return { eligible: false }; }   // could not close the earlier order: stay safe, no second discount
    }
  }
  return { eligible: true };
}

async function redeem(o, env) {
  const cd = o.customer_details || {};
  await sheet(env, "redeem", { phone: normPhone(cd.customer_phone), email: normEmail(cd.customer_email), order_id: o.order_id, amount: String(o.order_amount) });
}

/* ── helpers ── */
async function catalog(env) {
  if (catalogCache && Date.now() - catalogAt < 5 * 60 * 1000) return catalogCache;
  const r = await fetch(env.SITE_URL.replace(/\/$/, "") + "/assets/catalog.json", { cf: { cacheTtl: 300 } });
  if (!r.ok) throw new Error("catalog " + r.status);
  catalogCache = await r.json(); catalogAt = Date.now();
  return catalogCache;
}

async function cashfree(env, method, path, body) {
  const base = mode(env) === "production" ? "https://api.cashfree.com/pg" : "https://sandbox.cashfree.com/pg";
  const r = await fetch(base + path, {
    method,
    headers: {
      "x-api-version": env.CASHFREE_API_VERSION || API_VERSION,
      "x-client-id": env.CASHFREE_APP_ID,
      "x-client-secret": env.CASHFREE_SECRET,
      "Content-Type": "application/json", Accept: "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    console.error("cashfree", r.status, JSON.stringify(data));
    const e = new Error(r.status === 404 ? "Unknown order." : "The payment service could not start this payment. Please try again.");
    e.status = r.status === 404 ? 404 : 502; throw e;
  }
  return data;
}

function corsHeaders(request, env) {
  const origin = request.headers.get("Origin") || "";
  const allowed = [env.SITE_URL, "https://www.blushtinyblossoms.co.in", ...(env.ALLOWED_ORIGINS || "").split(",")]
    .map(s => (s || "").trim().replace(/\/$/, "")).filter(Boolean);
  const h = { "Access-Control-Allow-Methods": "GET, POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type", Vary: "Origin" };
  if (allowed.includes(origin)) h["Access-Control-Allow-Origin"] = origin;
  return h;
}

const mode = env => (env.CASHFREE_ENV === "production" ? "production" : "sandbox");
const json = (obj, status, headers) => new Response(JSON.stringify(obj), { status, headers: { ...headers, "Content-Type": "application/json" } });
const bad = msg => Object.assign(new Error(msg), { status: 400 });
const need = (ok, msg, status) => { if (!ok) throw Object.assign(new Error(msg), { status }); };
const clip = (s, n) => (s.length > n ? s.slice(0, n) : s.length < 3 ? (s + "   ").slice(0, 3) : s);
/* Cashfree rejects order_tags / order_note values with symbols, emojis, line breaks or URLs, so keep plain letters, digits and . - _ / only. */
const safeText = v => String(v == null ? "" : v).replace(/[\u2010-\u2015]/g, "-").replace(/\u00d7/g, "x").normalize("NFKD").replace(/[^A-Za-z0-9 .\-_\/]/g, " ").replace(/\s+/g, " ").trim();
function compactTags(o) { const out = {}; for (const [k, v] of Object.entries(o)) { const t = safeText(v).slice(0, 250); if (t) out[k] = t; } return out; }
function randomId(n) { const a = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789", b = crypto.getRandomValues(new Uint8Array(n)); return [...b].map(x => a[x % a.length]).join(""); }
async function hmacBase64(secret, msg) {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(msg));
  return btoa(String.fromCharCode(...new Uint8Array(sig)));
}
function timingSafeEqual(a, b) { if (a.length !== b.length) return false; let r = 0; for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i); return r === 0; }
