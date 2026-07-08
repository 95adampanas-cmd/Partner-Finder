// Partner Finder — frontend logic
const form = document.getElementById("form");
const urlInput = document.getElementById("url");
const btn = document.getElementById("btn");
const output = document.getElementById("output");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  let url = urlInput.value.trim();
  if (!url) return;
  if (!/^https?:\/\//i.test(url)) url = "https://" + url; // dopisz https:// jeśli brak

  output.hidden = false;
  output.innerHTML = loadingHTML();
  btn.disabled = true;

  try {
    const res = await fetch("/api/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();
    output.innerHTML = data.ok === false ? errorHTML(data.error) : resultHTML(data.result, url);
  } catch (err) {
    output.innerHTML = errorHTML(err.message);
  } finally {
    btn.disabled = false;
  }
});

function loadingHTML() {
  return `<div class="card loading">
    <div class="spinner"></div>
    <p>Analizuję firmę… (scrape strony → ocena → weryfikacja). Może potrwać ~20-40 s.</p>
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

// próbuje wyłuskać score z tekstu ("score: 9" albo "9/10")
function extractScore(text) {
  const m = text.match(/score[:\s]*([0-9]{1,2})/i) || text.match(/\b([0-9]{1,2})\s*\/\s*10\b/);
  if (m) {
    const n = parseInt(m[1], 10);
    if (n >= 1 && n <= 10) return n;
  }
  return null;
}
function scoreClass(n) { return n >= 7 ? "good" : n >= 5 ? "mid" : "bad"; }

// bezpieczne renderowanie: najpierw escape (anty-XSS), potem lekki markdown (**bold**)
function formatText(s) {
  return escapeHtml(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}
function escapeHtml(s) {
  return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}
function escapeAttr(s) { return escapeHtml(s).replace(/"/g, "&quot;"); }
