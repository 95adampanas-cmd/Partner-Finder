// Partner Finder — frontend logic
const form = document.getElementById("form");
const urlInput = document.getElementById("url");
const btn = document.getElementById("btn");
const output = document.getElementById("output");

let conversationId = null; // id sesji czatu (z /api/evaluate)

// podpowiedzi w czacie — pokazują userowi, o co MOŻE pytać
const SUGESTIE = [
  "Rozwiń synergię dla tej firmy",
  "Jak zbić ich najczęstsze obiekcje?",
  "Napisz draft pierwszej wiadomości do nich",
  "Który model współpracy najlepszy i dlaczego?",
];

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  let url = urlInput.value.trim();
  if (!url) return;
  if (!/^https?:\/\//i.test(url)) url = "https://" + url; // dopisz https:// jeśli brak

  output.hidden = false;
  output.innerHTML = loadingHTML();
  btn.disabled = true;
  conversationId = null;

  try {
    const res = await fetch("/api/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();
    if (data.ok === false) {
      output.innerHTML = errorHTML(data.error);
    } else {
      conversationId = data.conversation_id;
      output.innerHTML = resultHTML(data.result, url) + similarHTML() + chatHTML();
      mountChat();
      mountSimilar();
    }
  } catch (err) {
    output.innerHTML = errorHTML(err.message);
  } finally {
    btn.disabled = false;
  }
});

// ── Ocena ──
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
  const badge = score !== null
    ? `<div class="score ${scoreClass(score)}">${score}<span>/10</span></div>`
    : "";
  return `<div class="card result">
    <div class="result-head">
      <div class="mono"><span class="sq"></span> OCENA PARTNERSKA</div>
      ${badge}
    </div>
    <div class="result-body">${formatText(text)}</div>
    <a class="src" href="${escapeAttr(url)}" target="_blank" rel="noopener">${escapeHtml(url)} ↗</a>
  </div>`;
}

// ── Czat ──
function chatHTML() {
  const chips = SUGESTIE.map((s) => `<button class="chip" type="button">${escapeHtml(s)}</button>`).join("");
  return `<div class="card chat">
    <div class="mono"><span class="sq"></span> DOPYTAJ — RESEARCH NA ŻYWO</div>
    <p class="chat-hint">To nie koniec — możesz dopytać o tę firmę, branżę, synergię albo sposób rozmowy:</p>
    <div class="chips">${chips}</div>
    <div id="chat-messages" class="chat-messages"></div>
    <form id="chat-form" class="chat-input">
      <input id="chat-text" type="text" placeholder="Zapytaj o cokolwiek…" autocomplete="off">
      <button type="submit">Wyślij</button>
    </form>
  </div>`;
}

function mountChat() {
  const chatForm = document.getElementById("chat-form");
  const chatText = document.getElementById("chat-text");
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const msg = chatText.value.trim();
    if (msg) {
      chatText.value = "";
      sendChat(msg);
    }
  });
  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => sendChat(chip.textContent));
  });
}

async function sendChat(message) {
  const box = document.getElementById("chat-messages");
  box.insertAdjacentHTML("beforeend", msgHTML("user", message));
  const thinkingId = "think-" + Date.now();
  box.insertAdjacentHTML("beforeend", `<div id="${thinkingId}" class="msg bot thinking">pisze…</div>`);
  box.scrollTop = box.scrollHeight;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ conversation_id: conversationId, message }),
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
    <p class="chat-hint">Znajdź firmy z tej samej branży. Scoring odpalasz osobno dla każdej —
      płacisz tylko za te, które Cię interesują.</p>
    <button id="find-similar" class="find-btn" type="button">🔍 Znajdź 10 podobnych firm</button>
    <div id="similar-list" class="similar-list"></div>
  </div>`;
}

function mountSimilar() {
  document.getElementById("find-similar").addEventListener("click", findSimilar);
}

async function findSimilar() {
  const btn = document.getElementById("find-similar");
  const list = document.getElementById("similar-list");
  btn.disabled = true;
  btn.textContent = "Szukam podobnych… (~5 s)";
  list.innerHTML = "";
  try {
    const res = await fetch("/api/similar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ conversation_id: conversationId }),
    });
    const data = await res.json();
    if (data.ok === false) {
      list.innerHTML = `<p class="sim-err">⚠️ ${escapeHtml(data.error)}</p>`;
    } else if (!data.companies || data.companies.length === 0) {
      list.innerHTML = `<p class="sim-err">Nie znalazłem podobnych firm.</p>`;
    } else {
      list.innerHTML = data.companies.map(rowHTML).join("");
      document.querySelectorAll(".sim-row .ocen-btn").forEach((b) =>
        b.addEventListener("click", () => ocenRow(b))
      );
    }
  } catch (err) {
    list.innerHTML = `<p class="sim-err">⚠️ ${escapeHtml(err.message)}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "🔍 Znajdź 10 podobnych firm";
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

async function ocenRow(btn) {
  const row = btn.closest(".sim-row");
  const url = row.dataset.url;
  const box = row.querySelector(".sim-result");
  btn.disabled = true;
  btn.textContent = "Oceniam…";
  box.innerHTML = `<div class="spinner"></div>`;
  try {
    const res = await fetch("/api/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();
    if (data.ok === false) {
      box.innerHTML = `<p class="sim-err">⚠️ ${escapeHtml(data.error)}</p>`;
    } else {
      const score = extractScore(data.result);
      const badge = score !== null ? `<span class="score-mini ${scoreClass(score)}">${score}/10</span>` : "";
      box.innerHTML = `${badge}<div class="result-body">${formatText(data.result)}</div>`;
    }
  } catch (err) {
    box.innerHTML = `<p class="sim-err">⚠️ ${escapeHtml(err.message)}</p>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Oceń ponownie";
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
