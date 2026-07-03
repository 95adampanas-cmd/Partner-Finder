# ROADMAP — Partner Finder

> Fazy projektu i ich status. To jest wspólny tracker dla PM i Claude Code.
> Status: ⬜ do zrobienia · 🟡 w toku · ✅ zrobione

## Faza 0 — Setup 🟡
- ✅ Utworzenie repo na GitHub
- 🟡 Struktura folderów + dokumenty PM (PRD, ROADMAP, DECISIONS, BRAND)
- ⬜ Pierwszy commit + push na GitHub

## Faza 1 — Przepisanie na OpenAI Agents SDK ⬜
- ⬜ Przeniesienie logiki ze starego notebooka (`project.ipynb`) do `backend/`
- ⬜ Agent oceniający + tool `scrape_website` na `@function_tool`
- ⬜ Agent evaluator (jako guardrail lub osobny agent)
- ⬜ Tool `save_partner` (zapis do CSV)
- ⬜ Uruchomienie przez `Runner` — działa z linii komend

## Faza 2 — Nowe tools: szukanie partnerów ⬜
- ⬜ Decyzja: które API (Google Places / SerpAPI / Custom Search) — patrz DECISIONS.md
- ⬜ Tool: szukanie podobnych firm w Google / Clutch / Google Maps
- ⬜ Integracja z agentem (najpierw znajdź, potem oceń każdą)

## Faza 3 — Frontend ⬜
- ⬜ FastAPI: endpoint `POST /evaluate` (URL → JSON z oceną)
- ⬜ `frontend/index.html` + `app.js` — pole na URL, wyświetlanie wyniku
- ⬜ Branding Last Agency (patrz BRAND.md)
- ⬜ Spięcie front ↔ backend (CORS, fetch)

## Faza 4 — Prowadzenie jako PM ⬜
- ⬜ Regularne aktualizacje tego pliku i DECISIONS.md
- ⬜ Testy z realnymi firmami, zbieranie feedbacku
- ⬜ Retro: co zadziałało, co poprawić

---

**Aktualnie pracujemy nad:** Faza 0
