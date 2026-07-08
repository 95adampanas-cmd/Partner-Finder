# ROADMAP — Partner Finder

> Fazy projektu i ich status. To jest wspólny tracker dla PM i Claude Code.
> Status: ⬜ do zrobienia · 🟡 w toku · ✅ zrobione

## Faza 0 — Setup ✅
- ✅ Utworzenie repo na GitHub
- ✅ Struktura folderów + dokumenty PM (PRD, ROADMAP, DECISIONS, BRAND)
- ✅ Pierwszy commit + push na GitHub

## Faza 1 — Przepisanie na OpenAI Agents SDK ✅
- ✅ Tool `scrape_website` na `@function_tool`
- ✅ Tool `save_partner` (zapis do CSV)
- ✅ Agent oceniający (`Agent` + `Runner`) — działa w notebooku
- ✅ Kalibracja promptu scoringowego (kategorie, mocne sygnały, kotwica Tebim: 6→9)
- ✅ Agent evaluator (`agent_evaluator`, `output_type=Evaluator`) + `agent_rerun`
- ✅ Orkiestracja: `evaluator()`, `rerun()`, `run()` — pełny przepływ agent → evaluator → rerun
- ✅ Porządki: `partners.csv`, usunięty `print` z narzędzi, poprawiony prompt evaluatora

## Faza 2 — Nowe tools: szukanie firm (2 tryby) ⬜
- ⬜ Decyzja: które API (Google Places / SerpAPI / Custom Search) — patrz DECISIONS.md
- ⬜ Tool: szukanie firm (Google / Clutch / Google Maps)
- ⬜ Tryb 1 (od URL): wyciągnij branżę ze strony → znajdź do 10 podobnych → oceń każdą
- ⬜ Tryb 2 (od kryteriów): miasto + województwo + branża → znajdź do 10 firm → oceń każdą
- ⬜ Doprecyzowanie definicji „podobna firma" (open question w PRD)

## Faza 3 — Frontend ⬜
- ⬜ FastAPI: endpointy dla obu trybów (firma → oceny; kryteria → oceny)
- ⬜ `frontend/index.html` + `app.js` — wybór trybu, formularz, lista wyników
- ⬜ Branding Last Agency (patrz BRAND.md)
- ⬜ Spięcie front ↔ backend (CORS, fetch)

## Faza 4 — Prowadzenie jako PM ⬜
- ⬜ Regularne aktualizacje tego pliku i DECISIONS.md
- ⬜ Testy z realnymi firmami, zbieranie feedbacku
- ⬜ Retro: co zadziałało, co poprawić

---

**Aktualnie pracujemy nad:** Faza 2 — narzędzie `search_companies` (najpierw decyzja o API)

