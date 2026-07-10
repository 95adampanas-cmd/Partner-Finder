// Partner Finder — frontend (workspace z kartami)
const form = document.getElementById("form");
const urlInput = document.getElementById("url");
const btn = document.getElementById("btn");
const output = document.getElementById("output");

let tabs = [];       // [{id, nazwa, url}] — do paska kart
let activeId = null; // aktywna karta
let tabSeq = 0;      // licznik id kart

const SUGESTIE = [
  "Rozwiń synergię dla tej firmy",
  "Jak zbić ich najczęstsze obiekcje?",
  "Napisz draft pierwszej wiadomości do nich",
  "Który model współpracy najlepszy i dlaczego?",
];

// ── Ocena głównej firmy (nowa sesja researchu) ──
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  let url = urlInput.value.trim();
  if (!url) return;
  if (!/^https?:\/\//i.test(url)) url = "https://" + url;

  output.hidden = false;
  output.innerHTML = loadingHTML();
  btn.disabled = true;

  try {
    const data = await evaluate(url);
    if (data.ok === false) {
      output.innerHTML = errorHTML(data.error);
    } else {
      // reset workspace i otwórz pierwszą kartę
      tabs = [];
      activeId = null;
      output.innerHTML = `<div id="tabbar" class="tabbar"></div><div id="panels"></div>`;
      openTab(data.result, url, data.conversation_id);
    }
  } catch (err) {
    output.innerHTML = errorHTML(err.message);
  } finally {
    btn.disabled = false;
  }
});

async function evaluate(url) {
  const res = await fetch("/api/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  return res.json();
}

// ── Karty ──
function openTab(result, url, cid) {
  const id = "tab" + ++tabSeq;
  tabs.push({ id, nazwa: labelFromUrl(url), url });
  document.getElementById("panels").insertAdjacentHTML("beforeend", panelHTML(id, result, url, cid));
  setActive(id);
}

function setActive(id) {
  activeId = id;
  document.querySelectorAll("#panels .panel").forEach((p) => {
    p.style.display = p.dataset.id === id ? "block" : "none";
  });
  renderTabBar();
}

function closeTab(id) {
  tabs = tabs.filter((t) => t.id !== id);
  document.querySelector(`#panels .panel[data-id="${id}"]`)?.remove();
  if (activeId === id) {
    activeId = tabs.length ? tabs[tabs.length - 1].id : null;
    if (activeId) setActive(activeId);
    else renderTabBar();
  } else {
    renderTabBar();
  }
}

function renderTabBar() {
  const bar = document.getElementById("tabbar");
  if (!bar) return;
  bar.innerHTML = tabs
    .map(
      (t) => `<div class="tab ${t.id === activeId ? "active" : ""}" data-id="${t.id}">
        <span class="tab-name">${escapeHtml(t.nazwa)}</span>
        <span class="tab-close" data-close="${t.id}" title="Zamknij">×</span>
      </div>`
    )
    .join("");
}

// panel karty = ocena + czat + sekcja "podobne"
function panelHTML(id, result, url, cid) {
  return `<div class="panel" data-id="${id}" data-cid="${escapeAttr(cid)}">
    ${resultHTML(result, url)}
    ${chatBlockHTML(cid)}
    ${similarHTML()}
  </div>`;
}

// ── Event delegation ──
output.addEventListener("click", (e) => {
  const closeEl = e.target.closest(".tab-close");
  if (closeEl) { closeTab(closeEl.dataset.close); return; }
  const tabEl = e.target.closest(".tab");
  if (tabEl) { setActive(tabEl.dataset.id); return; }
  if (e.target.classList.contains("find-btn")) { findSimilar(e.target); return; }
  if (e.target.classList.contains("ocen-btn")) { ocenRow(e.target); return; }
  if (e.target.classList.contains("chip")) {
    sendChat(e.target.closest(".chat-block"), e.target.textContent);
  }
});

output.addEventListener("submit", (e) => {
  if (e.target.classList.contains("chat-form")) {
    e.preventDefault();
    const input = e.target.querySelector(".chat-text");
    const msg = input.value.trim();
    if (msg) {
      input.value = "";
      sendChat(e.target.closest(".chat-block"), msg);
    }
  }
});

// ── Widoki ──
function loadingHTML() {
  return `<div class="card loading">
    <div class="spinner"></div>
    <p>Analizuję firmę… (scrape → ocena → synergia → jak rozmawiać). Może potrwać ~30-60 s.</p>
  </div>`;
}

function errorHTML(msg) {
  return `<div class="card error">
    <div class="mono"><span class="sq"></span> BŁĄD</div>
    <p>${escapeHtml(msg)}</p>
  </div>`;
}

function resultHTML(text, url) {
  const score = extractScore(text);
  const badge = score !== null ? `<div class="score ${scoreClass(score)}">${score}<span>/10</span></div>` : "";
  return `<div class="card result">
    <div class="result-head">
      <div class="mono"><span class="sq"></span> OCENA PARTNERSKA</div>
      ${badge}
    </div>
    <div class="result-body">${formatText(text)}</div>
    <a class="src" href="${escapeAttr(url)}" target="_blank" rel="noopener">${escapeHtml(url)} ↗</a>
  </div>`;
}

// ── Czat (przypięty do firmy przez data-cid) ──
function chatBlockHTML(cid) {
  const chips = SUGESTIE.map((s) => `<button class="chip" type="button">${escapeHtml(s)}</button>`).join("");
  return `<div class="card chat chat-block" data-cid="${escapeAttr(cid)}">
    <div class="mono"><span class="sq"></span> DOPYTAJ O TĘ FIRMĘ</div>
    <p class="chat-hint">Możesz dopytać o tę firmę, branżę, synergię albo sposób rozmowy:</p>
    <div class="chips">${chips}</div>
    <div class="chat-messages"></div>
    <form class="chat-form chat-input">
      <input class="chat-text" type="text" placeholder="Zapytaj o cokolwiek…" autocomplete="off">
      <button type="submit">Wyślij</button>
    </form>
  </div>`;
}

async function sendChat(block, message) {
  const cid = block.dataset.cid;
  const box = block.querySelector(".chat-messages");
  box.insertAdjacentHTML("beforeend", msgHTML("user", message));
  const thinkingId = "think-" + Date.now();
  box.insertAdjacentHTML("beforeend", `<div id="${thinkingId}" class="msg bot thinking">pisze…</div>`);
  box.scrollTop = box.scrollHeight;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ conversation_id: cid, message }),
    });
    const data = await res.json();
    document.getElementById(thinkingId)?.remove();
    box.insertAdjacentHTML("beforeend", msgHTML("bot", data.ok === false ? "⚠️ " + data.error : data.reply));
  } catch (err) {
    document.getElementById(thinkingId)?.remove();
    box.insertAdjacentHTML("beforeend", msgHTML("bot", "⚠️ " + err.message));
  }
  box.scrollTop = box.scrollHeight;
}

function msgHTML(who, text) {
  return `<div class="msg ${who}">${formatText(text)}</div>`;
}

// ── Podobne firmy (Tavily) ──
function similarHTML() {
  return `<div class="card similar">
    <div class="mono"><span class="sq"></span> PODOBNE FIRMY</div>
    <p class="chat-hint">Znajdź firmy z tej samej branży. Każda oceniona otworzy się w nowej karcie —
      płacisz tylko za te, które Cię interesują.</p>
    <button class="find-btn" type="button">🔍 Znajdź 10 podobnych firm</button>
    <div class="similar-list"></div>
  </div>`;
}

async function findSimilar(btnEl) {
  const panel = btnEl.closest(".panel");
  const cid = panel.dataset.cid;
  const list = panel.querySelector(".similar-list");
  btnEl.disabled = true;
  btnEl.textContent = "Szukam podobnych… (~5 s)";
  list.innerHTML = "";
  try {
    const res = await fetch("/api/similar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ conversation_id: cid }),
    });
    const data = await res.json();
    if (data.ok === false) {
      list.innerHTML = `<p class="sim-err">⚠️ ${escapeHtml(data.error)}</p>`;
    } else if (!data.companies || data.companies.length === 0) {
      list.innerHTML = `<p class="sim-err">Nie znalazłem podobnych firm.</p>`;
    } else {
      list.innerHTML = data.companies.map(rowHTML).join("");
    }
  } catch (err) {
    list.innerHTML = `<p class="sim-err">⚠️ ${escapeHtml(err.message)}</p>`;
  } finally {
    btnEl.disabled = false;
    btnEl.textContent = "🔍 Znajdź 10 podobnych firm";
  }
}

function rowHTML(firma) {
  return `<div class="sim-row" data-url="${escapeAttr(firma.url)}">
    <div class="sim-info">
      <span class="sim-name">${escapeHtml(firma.nazwa)}</span>
      <a class="sim-url" href="${escapeAttr(firma.url)}" target="_blank" rel="noopener">${escapeHtml(firma.url)} ↗</a>
    </div>
    <button class="ocen-btn" type="button">Oceń →</button>
  </div>`;
}

async function ocenRow(btnEl) {
  const row = btnEl.closest(".sim-row");
  const url = row.dataset.url;
  btnEl.disabled = true;
  btnEl.textContent = "Oceniam… (~40 s)";
  try {
    const data = await evaluate(url);
    if (data.ok === false) {
      btnEl.disabled = false;
      btnEl.textContent = "Oceń ponownie";
      row.insertAdjacentHTML("beforeend", `<p class="sim-err">⚠️ ${escapeHtml(data.error)}</p>`);
    } else {
      openTab(data.result, url, data.conversation_id); // otwiera nową kartę i przełącza
      btnEl.textContent = "✓ Otwarto kartę";
    }
  } catch (err) {
    btnEl.disabled = false;
    btnEl.textContent = "Oceń ponownie";
    row.insertAdjacentHTML("beforeend", `<p class="sim-err">⚠️ ${escapeHtml(err.message)}</p>`);
  }
}

// ── Pomocnicze ──
function labelFromUrl(url) {
  try { return new URL(url).hostname.replace(/^www\./, ""); }
  catch { return url; }
}
function extractScore(text) {
  const m = text.match(/score[:\s]*([0-9]{1,2})/i) || text.match(/\b([0-9]{1,2})\s*\/\s*10\b/);
  if (m) {
    const n = parseInt(m[1], 10);
    if (n >= 1 && n <= 10) return n;
  }
  return null;
}
function scoreClass(n) { return n >= 7 ? "good" : n >= 5 ? "mid" : "bad"; }

function formatText(s) {
  return escapeHtml(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}
function escapeHtml(s) {
  return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}
function escapeAttr(s) { return escapeHtml(s).replace(/"/g, "&quot;"); }
