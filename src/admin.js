/* Blush Tiny Blossoms — admin page script (/admin). Talks to the checkout service, which saves to GitHub.
   Nothing here is secret: the password is checked by the service, never by this page. */
(function () {
  const root = document.getElementById("admin");
  const CFG = JSON.parse(root.dataset.cfg), API = CFG.api.replace(/\/$/, "");
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const money = n => "₹" + Number(n).toLocaleString("en-IN");
  const SIZES = CFG.sizes, BANDS = CFG.bands;
  const POS = [["50% 15%", "Top (keep the face in view)"], ["50% 30%", "Upper"], ["50% 50%", "Centre"], ["50% 70%", "Lower"]];

  let pw = "", looks = [], rev = "", lastCommit = "", photos = new Set(), saved = "", uploads = {}; // uploads: name → { data (base64), url (preview) }
  try { pw = sessionStorage.getItem("blush.admin") || ""; } catch (e) {}

  const call = async (path, opts = {}) => {
    const r = await fetch(API + path, { ...opts, headers: { "Content-Type": "application/json", Authorization: "Bearer " + pw, ...(opts.headers || {}) } });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) { const e = new Error(d.error || "Something went wrong (" + r.status + ")."); e.status = r.status; throw e; }
    return d;
  };
  const dirty = () => JSON.stringify(looks) !== saved || Object.keys(uploads).length > 0;
  const allOut = l => SIZES.every(s => (l.soldout || []).includes(s));
  const salePrice = (p, l) => (l.discountPct ? Math.round(p * (100 - l.discountPct) / 100) : p);
  const thumb = l => (uploads[l.id] ? uploads[l.id].url : photos.has(l.id) ? CFG.site + "/img/" + l.id + "-480.webp" : "");

  /* ── sign in ── */
  const login = $("#ad-login"), app = $("#ad-app"), lerr = $("#ad-login-err");
  const load = async () => {
    const d = await call("/admin/looks");
    looks = d.looks; rev = d.rev; photos = new Set(d.photos); saved = JSON.stringify(looks); uploads = {};
    login.hidden = true; app.hidden = false; render(); status();
  };
  login.addEventListener("submit", async e => {
    e.preventDefault(); lerr.textContent = ""; pw = $("#ad-pw").value;
    const b = $("button", login); b.disabled = true;
    try { await load(); try { sessionStorage.setItem("blush.admin", pw); } catch (x) {} }
    catch (x) { lerr.textContent = x.status === 401 ? "Wrong password." : x.message; }
    b.disabled = false;
  });
  if (pw) load().catch(() => { pw = ""; });
  $("#ad-out").addEventListener("click", () => { try { sessionStorage.removeItem("blush.admin"); } catch (e) {} location.reload(); });
  window.addEventListener("beforeunload", e => { if (dirty()) { e.preventDefault(); e.returnValue = ""; } });

  /* ── list ── */
  const list = $("#ad-list"), bar = $("#ad-bar"), barMsg = $("#ad-bar-msg");
  function render() {
    list.innerHTML = looks.map((l, i) => {
      const t = thumb(l), out = allOut(l), n = (l.soldout || []).length;
      const chips = [
        l.hidden ? '<span class="chip grey">Hidden</span>' : "",
        out ? '<span class="chip dark">Sold out</span>' : n ? '<span class="chip">' + n + " size" + (n > 1 ? "s" : "") + " sold out</span>" : "",
        l.discountPct ? '<span class="chip rose">' + l.discountPct + "% off</span>" : "",
        l.new ? '<span class="chip">New</span>' : "",
        l.restock ? '<span class="chip">Back in stock</span>' : "",
      ].join("");
      const price = l.prices ? (l.discountPct ? "<s>" + money(Math.min(...l.prices)) + "</s> " : "") + "From " + money(salePrice(Math.min(...l.prices), l)) : "Price on request";
      return '<div class="ad-row' + (l.hidden ? " off" : "") + '">' +
        (t ? '<img src="' + esc(t) + '" alt="" style="object-position:' + esc(l.pos || "50% 30%") + '">' : '<div class="noimg">No photo</div>') +
        '<div class="ad-main"><b>' + esc(l.name) + (l.variant ? " · " + esc(l.variant) : "") + '</b><span>' + price + '</span><div class="chips">' + chips + "</div></div>" +
        '<div class="ad-acts"><div class="ad-ord"><button type="button" data-up="' + i + '" aria-label="Move ' + esc(l.name) + ' up"' + (i ? "" : " disabled") + '>▲</button>' +
        '<input type="number" inputmode="numeric" min="1" max="' + looks.length + '" value="' + (i + 1) + '" data-rank="' + i + '" aria-label="Position of ' + esc(l.name) + '">' +
        '<button type="button" data-down="' + i + '" aria-label="Move ' + esc(l.name) + ' down"' + (i < looks.length - 1 ? "" : " disabled") + '>▼</button></div>' +
        '<button type="button" class="btn ghost" data-edit="' + i + '">Edit</button>' +
        '<button type="button" class="linkbtn" data-out="' + i + '">' + (out ? "Mark available" : "Mark sold out") + "</button></div></div>";
    }).join("");
    bar.classList.toggle("on", dirty());
    barMsg.textContent = dirty() ? "You have changes that are not on the website yet." : "";
  }
  list.addEventListener("click", e => {
    const ed = e.target.closest("[data-edit]"), so = e.target.closest("[data-out]"), up = e.target.closest("[data-up]"), dn = e.target.closest("[data-down]");
    if (up) move(+up.dataset.up, +up.dataset.up - 1, "up");
    if (dn) move(+dn.dataset.down, +dn.dataset.down + 1, "down");
    if (ed) openEditor(+ed.dataset.edit);
    if (so) { const l = looks[+so.dataset.out]; if (allOut(l)) delete l.soldout; else l.soldout = SIZES.slice(); render(); }
  });
  /* order: the list order is the order on the website (New looks are lifted to the front when the site is built) */
  function move(from, to, focus) {
    to = Math.max(0, Math.min(looks.length - 1, to));
    if (to === from || !(to >= 0)) { render(); return; }
    looks.splice(to, 0, looks.splice(from, 1)[0]); render();
    const el = focus && list.querySelector("[data-" + focus + '="' + to + '"]');
    if (el && !el.disabled) el.focus(); else if (focus) { const r = list.querySelector('[data-rank="' + to + '"]'); if (r) r.focus(); }
  }
  list.addEventListener("change", e => { const r = e.target.closest("[data-rank]"); if (r) move(+r.dataset.rank, Math.round(Number(r.value) || 0) - 1); });
  list.addEventListener("keydown", e => { if (e.key === "Enter" && e.target.closest("[data-rank]")) { e.preventDefault(); e.target.blur(); } });
  $("#ad-new").addEventListener("click", () => openEditor(-1));
  $("#ad-discard").addEventListener("click", () => { looks = JSON.parse(saved); uploads = {}; render(); });

  /* ── editor ── */
  const dlg = $("#ad-edit"), f = $("#ad-form"), eerr = $("#ad-edit-err");
  let cur = -1, pend = {}; // pend: photos chosen in this editor session
  const slug = s => s.toLowerCase().normalize("NFKD").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60);
  function openEditor(i) {
    cur = i; pend = {}; eerr.textContent = "";
    const l = i < 0 ? { name: "", cat: [], pos: "50% 30%", new: true } : looks[i];
    $("#ad-edit-title").textContent = i < 0 ? "Add a new look" : "Edit " + l.name;
    f.name.value = l.name || ""; f.variant.value = l.variant || ""; f.sil.value = l.sil || ""; f.pal.value = l.pal || "";
    f.contents.value = l.contents || ""; f.fabric.value = l.fabric || ""; f.detail.value = l.detail || ""; f.styling.value = l.styling || "";
    BANDS.forEach((_, k) => (f["p" + k].value = l.prices ? l.prices[k] : ""));
    f.discountPct.value = l.discountPct || "";
    $$("[name=cat]", f).forEach(c => (c.checked = (l.cat || []).includes(c.value)));
    $$("[name=so]", f).forEach(c => (c.checked = (l.soldout || []).includes(c.value)));
    f.pos.value = POS.some(p => p[0] === l.pos) ? l.pos : "50% 30%";
    f.isnew.checked = !!l.new; f.restock.checked = !!l.restock && !l.new; f.hidden.checked = !!l.hidden;
    f.photo.value = ""; f.more.value = "";
    const t = i < 0 ? "" : thumb(l);
    $("#ad-photo-prev").innerHTML = t ? '<img src="' + esc(t) + '" alt="">' : "<span>No photo yet</span>";
    $("#ad-more-note").textContent = "";
    $("#ad-del").hidden = i < 0;
    paintSale(); dlg.showModal();
  }
  const paintSale = () => {
    const p = Number(f.p0.value), d = Number(f.discountPct.value);
    $("#ad-sale-note").textContent = p && d > 0 && d <= 90 ? "Shows as " + money(Math.round(p * (100 - d) / 100)) + " with " + money(p) + " struck through (first size band)." : "Leave empty for no discount.";
  };
  f.addEventListener("input", paintSale);
  /* the first band's price sets the other four (first + 1000 / 1500 / 2000 / 2500); they stay editable */
  const STEPS = CFG.steps || [0, 1000, 1500, 2000, 2500];
  f.p0.addEventListener("input", () => {
    const x = Math.round(Number(f.p0.value));
    STEPS.forEach((s, k) => { if (k) f["p" + k].value = x >= 1 ? x + s : ""; });
  });
  f.isnew.addEventListener("change", () => { if (f.isnew.checked) f.restock.checked = false; });   // one tag at a time
  f.restock.addEventListener("change", () => { if (f.restock.checked) f.isnew.checked = false; });
  $("#ad-so-all").addEventListener("click", () => $$("[name=so]", f).forEach(c => (c.checked = true)));
  $("#ad-so-none").addEventListener("click", () => $$("[name=so]", f).forEach(c => (c.checked = false)));
  $("#ad-cancel").addEventListener("click", () => dlg.close());
  $("#ad-del").addEventListener("click", () => {
    const b = $("#ad-del");
    if (b.dataset.sure !== "1") { b.dataset.sure = "1"; b.textContent = "Tap again to remove this look"; setTimeout(() => { b.dataset.sure = ""; b.textContent = "Remove this look"; }, 4000); return; }
    b.dataset.sure = ""; b.textContent = "Remove this look";
    const id = looks[cur].id; looks.splice(cur, 1); Object.keys(uploads).forEach(k => { if (k === id || k.startsWith(id + "-")) delete uploads[k]; });
    dlg.close(); render();
  });

  /* photos are shrunk in the browser before upload, so phone pictures of any size work */
  const shrink = file => new Promise((res, rej) => {
    const img = new Image(), url = URL.createObjectURL(file);
    img.onload = () => {
      const k = Math.min(1, 1800 / Math.max(img.width, img.height)), c = document.createElement("canvas");
      c.width = Math.round(img.width * k); c.height = Math.round(img.height * k);
      const x = c.getContext("2d"); x.fillStyle = "#fff"; x.fillRect(0, 0, c.width, c.height); x.drawImage(img, 0, 0, c.width, c.height);
      URL.revokeObjectURL(url);
      const data = c.toDataURL("image/jpeg", 0.9);
      res({ data: data.split(",")[1], url: data });
    };
    img.onerror = () => { URL.revokeObjectURL(url); rej(new Error("That file is not a photo this page can read. Use a JPG or PNG.")); };
    img.src = url;
  });
  f.photo.addEventListener("change", async () => {
    eerr.textContent = ""; if (!f.photo.files[0]) return;
    try { pend.main = await shrink(f.photo.files[0]); $("#ad-photo-prev").innerHTML = '<img src="' + pend.main.url + '" alt="">'; }
    catch (x) { eerr.textContent = x.message; f.photo.value = ""; }
  });
  f.more.addEventListener("change", async () => {
    eerr.textContent = "";
    try { pend.more = []; for (const file of [...f.more.files].slice(0, 6)) pend.more.push(await shrink(file)); $("#ad-more-note").textContent = pend.more.length + " extra photo" + (pend.more.length === 1 ? "" : "s") + " will be added to the gallery."; }
    catch (x) { eerr.textContent = x.message; f.more.value = ""; pend.more = []; }
  });

  f.addEventListener("submit", e => {
    e.preventDefault(); eerr.textContent = "";
    const name = f.name.value.trim(), variant = f.variant.value.trim();
    if (name.length < 2) { eerr.textContent = "Please enter the name."; f.name.focus(); return; }
    const raw = BANDS.map((_, k) => f["p" + k].value.trim());
    let prices = null;
    if (raw.some(v => v)) {
      prices = raw.map(v => Math.round(Number(v)));
      if (prices.some(n => !(n >= 1))) { eerr.textContent = "Enter a price for all five size bands, or leave all five empty for “Price on request”."; f.p0.focus(); return; }
    }
    const d = Math.round(Number(f.discountPct.value) || 0);
    if (d < 0 || d > 90) { eerr.textContent = "The discount must be between 0 and 90%."; f.discountPct.focus(); return; }
    let l = cur < 0 ? {} : looks[cur];
    if (cur < 0) {
      let id = slug(name + (variant ? " " + variant : "")), n = 2;
      if (!id) { eerr.textContent = "Please use letters or numbers in the name."; return; }
      const base = id; while (looks.some(x => x.id === id)) id = base + "-" + n++;
      if (!pend.main) { eerr.textContent = "Please choose the main photo."; return; }
      l.id = id;
    }
    Object.assign(l, { name, sil: f.sil.value.trim(), pal: f.pal.value.trim(), cat: $$("[name=cat]:checked", f).map(c => c.value), contents: f.contents.value.trim(),
      pos: f.pos.value, fabric: f.fabric.value.trim(), detail: f.detail.value.trim() });
    const set = (k, v) => { if (v) l[k] = v; else delete l[k]; };
    set("variant", variant); set("styling", f.styling.value.trim()); set("prices", prices); set("discountPct", prices && d ? d : 0);
    set("new", f.isnew.checked); set("restock", f.restock.checked); set("hidden", f.hidden.checked);
    const so = $$("[name=so]:checked", f).map(c => c.value); set("soldout", so.length ? so : 0);
    if (pend.main) uploads[l.id] = pend.main;
    if (pend.more && pend.more.length) {
      let n = 2; const taken = k => photos.has(l.id + "-" + k) || uploads[l.id + "-" + k];
      pend.more.forEach(p => { while (taken(n)) n++; uploads[l.id + "-" + n] = p; n++; });
    }
    if (cur < 0) looks.push(l);
    dlg.close(); render();
  });

  /* ── publish ── */
  const pub = $("#ad-publish"), stat = $("#ad-status");
  pub.addEventListener("click", async () => {
    if (!dirty()) return;
    const names = Object.keys(uploads);
    if (names.length > 12) { barMsg.textContent = "Please publish at most 12 new photos at a time."; return; }
    pub.disabled = true; barMsg.textContent = "Saving…";
    try {
      const d = await call("/admin/publish", { method: "POST", body: JSON.stringify({ looks, rev, images: names.map(n => ({ name: n, data: uploads[n].data })), message: "Update the collection" }) });
      rev = d.rev; lastCommit = d.commit; names.forEach(n => photos.add(n)); saved = JSON.stringify(looks); uploads = {};
      render(); stat.textContent = "Saved. The website is rebuilding; this takes a few minutes."; watch(0);
    } catch (x) { barMsg.textContent = x.message; }
    pub.disabled = false;
  });
  async function status() {
    try {
      const s = await call("/admin/status");
      if (s.status === "none") { stat.textContent = ""; return "none"; }
      const when = new Date(s.started).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" });
      if (s.status !== "completed") { stat.textContent = "The website is rebuilding (started " + when + ")…"; return "busy"; }
      stat.textContent = s.conclusion === "success" ? "Website last rebuilt " + when + ". New changes show within a few minutes of that." : "The last rebuild failed (" + when + "). The website still shows the previous version. Tell Claude: “the site build failed”.";
      return s.conclusion !== "success" ? "failed" : !lastCommit || s.commit === lastCommit ? "done" : "old";
    } catch (e) { return "error"; }
  }
  function watch(n) { if (n > 40) return; setTimeout(async () => { const s = await status(); if (s === "busy" || s === "old" || s === "none") watch(n + 1); }, 10000); }
})();
