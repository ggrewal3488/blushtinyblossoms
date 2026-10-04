/**
 * Blush Tiny Blossoms: customer list + welcome-offer ledger, kept in the BlushTinyBlossoms Google Sheet.
 *
 * Set up (once):
 *   1. Open the Google Sheet → Extensions → Apps Script. Delete what is there and paste this whole file.
 *   2. Change KEY below to a long phrase of your own (letters and digits, 20+ characters). Keep it private.
 *   3. Deploy → New deployment → type "Web app" → Execute as: Me → Who has access: Anyone → Deploy.
 *      Approve the permission prompt. Copy the "Web app URL" (it ends in /exec).
 *   4. In Cloudflare → the checkout worker → Settings → Variables and Secrets, add
 *        SHEET_API  = that Web app URL
 *        SHEET_KEY  = the same phrase as KEY (type: Secret)
 *      then Deploy the worker.
 *   After any later edit to this script: Deploy → Manage deployments → Edit → Version: New version → Deploy.
 *
 * The script adds a "Customers" tab with one row per person:
 *   Signed up | Name | Mobile | Email | Status | Order ID | Paid amount | Updated | Page
 * Status is "Signed up", "Order started" or "Used". A row marked "Used" never gets the discount again.
 */
const KEY = "CHANGE-ME-to-a-long-private-phrase";
const TAB = "Customers";
const HEAD = ["Signed up", "Name", "Mobile", "Email", "Status", "Order ID", "Paid amount", "Updated", "Page"];

function doPost(e) {
  let out;
  try {
    const b = JSON.parse(e.postData.contents || "{}");
    if (KEY.indexOf("CHANGE-ME") === 0 || b.key !== KEY) return reply({ ok: false, error: "forbidden" });
    const lock = LockService.getScriptLock();
    lock.waitLock(20000);
    try { out = handle(b); } finally { lock.releaseLock(); }
  } catch (err) { out = { ok: false, error: String(err) }; }
  return reply(out);
}

function doGet() { return reply({ ok: true, service: "blush customers" }); }

function handle(b) {
  const sh = tab(), now = new Date();
  const phone = String(b.phone || "").replace(/\D/g, "").slice(-10), email = String(b.email || "").trim().toLowerCase();
  const rows = sh.getLastRow() > 1 ? sh.getRange(2, 1, sh.getLastRow() - 1, HEAD.length).getValues() : [];
  // every row that shares the mobile number or the email
  const hits = [];
  rows.forEach(function (r, i) {
    const p = String(r[2]).replace(/\D/g, "").slice(-10), m = String(r[3]).trim().toLowerCase();
    if ((phone && p === phone) || (email && m === email)) hits.push(i);
  });
  const statusOf = function () {
    if (!hits.length) return { status: "none" };
    if (hits.some(function (i) { return rows[i][4] === "Used"; })) return { status: "used" };
    const pend = hits.filter(function (i) { return rows[i][4] === "Order started" && rows[i][5]; })[0];
    if (pend !== undefined) return { status: "pending", order_id: String(rows[pend][5]) };
    return { status: "signed" };
  };
  const setRow = function (i, status, orderId, amount) {
    const r = i + 2;
    sh.getRange(r, 5).setValue(status);
    if (orderId !== undefined) sh.getRange(r, 6).setValue(orderId);
    if (amount !== undefined) sh.getRange(r, 7).setValue(amount);
    sh.getRange(r, 8).setValue(now);
    if (phone && !String(rows[i][2])) sh.getRange(r, 3).setNumberFormat("@").setValue(phone);
    if (email && !String(rows[i][3])) sh.getRange(r, 4).setValue(email);
  };

  if (b.action === "check") return Object.assign({ ok: true }, statusOf());

  if (b.action === "signup") {
    const st = statusOf();
    if (st.status === "none") {
      const r = sh.getLastRow() + 1;
      sh.getRange(r, 3).setNumberFormat("@");
      sh.getRange(r, 1, 1, HEAD.length).setValues([[now, String(b.name || "").slice(0, 80), phone, email, "Signed up", "", "", now, String(b.page || "").slice(0, 80)]]);
      return { ok: true, status: "new" };
    }
    // already known: fill in an email we did not have, keep the first sign-up
    if (email) hits.forEach(function (i) { if (!String(rows[i][3])) sh.getRange(i + 2, 4).setValue(email); });
    return { ok: true, status: st.status === "used" ? "used" : "exists" };
  }

  if (b.action === "reserve") {
    hits.forEach(function (i) { if (rows[i][4] !== "Used") setRow(i, "Order started", String(b.order_id || "")); });
    return { ok: true };
  }

  if (b.action === "redeem") {
    hits.forEach(function (i) { setRow(i, "Used", String(b.order_id || ""), String(b.amount || "")); });
    return { ok: true };
  }
  return { ok: false, error: "unknown action" };
}

function tab() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(TAB);
  if (!sh) {
    sh = ss.insertSheet(TAB);
    sh.getRange(1, 1, 1, HEAD.length).setValues([HEAD]).setFontWeight("bold");
    sh.setFrozenRows(1);
    sh.getRange("C:C").setNumberFormat("@");
  }
  return sh;
}

function reply(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
