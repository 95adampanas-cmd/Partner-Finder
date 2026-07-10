// Partner Finder — frontend logic
const form = document.getElementById("form");
const urlInput = document.getElementById("url");
const btn = document.getElementById("btn");
const output = document.getElementById("output");

let mainCid = null; // conversation_id głównej firmy (do szukania podobnych)

// podpowiedzi w czacie — pokazują userowi, o co MOŻE pytać
const SUGESTIE = [
  "Rozwiń synergię dla tej firmy",
  "Jak zbić ich najczęstsze obiekcje?",
  "Napisz draft pierwszej wiadomości do nich",
  "Który model współpracy najlepszy i dlaczego?",
];

// ── Ocena głównej firmy ──
form.addEventListener("submit", async (e) => {
  e.preventDefault();
  let url = urlInput.value.trim();
  if (!url) return;
  if (!/^https?:\/\//i.test(url)) url = "https://" + url;

  output.hidden = false;
  output.innerHTML = loadingHTML();
  btn.disabled = true;
  mainCid = null;

  try {
    const data = await evaluate(url);
    if (data.ok === false) {
      output.innerHTML = errorHTML(data.error);
    } else {
      mainCid = data.conversation_id;
      output.innerHTML = companyBlockHTML(data.result, url, data.conversation_id) + similarHTML();
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

// ── Event delegation (jeden listener na wszystkie firmy/czaty) ──
output.addEventListener("submit", (e) => {
  if (e.target.classList.contains("chat-form")) {
    e.preventDefault();
    const block = e.target.closest(".chat-block");
    const input = e.target.querySelector(".chat-text");
    const msg = input.value.trim();
    if (msg) {
      input.value = "";
      sendChat(block, msg);
    }
  }
});

output.addEventListener("click", (e) => {
  if (e.target.classList.contains("chip")) {
    sendChat(e.target.closest(".chat-block"), e.target.textContent);
  } else if (e.target.id === "find-similar") {
    findSimilar();
  } else if (e.target.classList.contains("ocen-btn")) {
    ocenRow(e.target);
  }
});

// ── Bloki widoku ──
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

// pełny blok firmy = ocena + własny czat (przypięty do jej conversation_id)
function companyBlockHTML(text, url, cid) {
  return resultHTML(text, url) + chatBlockHTML(cid);
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

// czat przypięty do KONKRETNEJ firmy (data-cid)
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
    <p class="chat-hint">Znajdź firmy z tej samej branży. Scoring (i czat) odpalasz osobno dla każdej —
      płacisz tylko za te, które Cię interesują.</p>
    <button id="find-similar" class="find-btn" type="button">🔍 Znajdź 10 podobnych firm</button>
    <div id="similar-list" class="similar-list"></div>
  </div>`;
}

async function findSimilar() {
  const btnEl = document.getElementById("find-similar");
  const list = document.getElementById("similar-list");
  btnEl.disabled = true;
  btnEl.textContent = "Szukam podobnych… (~5 s)";
  list.innerHTML = "";
  try {
    const res = await fetch("/api/similar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ conversation_id: mainCid }),
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
    <div class="sim-head">
      <div class="sim-info">
        <span class="sim-name">${escapeHtml(firma.nazwa)}</span>
        <a class="sim-url" href="${escapeAttr(firma.url)}" target="_blank" rel="noopener">${escapeHtml(firma.url)} ↗</a>
      </div>
      <button class="ocen-btn" type="button">Oceń →</button>
    </div>
    <div class="sim-result"></div>
  </div>`;
}

async function ocenRow(btnEl) {
  const row = btnEl.closest(".sim-row");
  const url = row.dataset.url;
  const box = row.querySelector(".sim-result");
  btnEl.disabled = true;
  btnEl.textContent = "Oceniam…";
  box.innerHTML = `<div class="spinner"></div>`;
  try {
    const data = await evaluate(url);
    if (data.ok === false) {
      box.innerHTML = `<p class="sim-err">⚠️ ${escapeHtml(data.error)}</p>`;
      btnEl.textContent = "Oceń ponownie";
    } else {
      // ocena + WŁASNY czat tej firmy (jej conversation_id)
      box.innerHTML = companyBlockHTML(data.result, url, data.conversation_id);
      btnEl.textContent = "✓ Ocenione";
    }
  } catch (err) {
    box.innerHTML = `<p class="sim-err">⚠️ ${escapeHtml(err.message)}</p>`;
    btnEl.textContent = "Oceń ponownie";
  } finally {
    btnEl.disabled = false;
  }
}

// ── Pomocnicze ──
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
