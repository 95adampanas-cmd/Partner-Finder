# DECISIONS — log decyzji

> Zapisujemy tu WAŻNE decyzje i ich uzasadnienie ("czemu tak, a nie inaczej").
> Dzięki temu za miesiąc pamiętasz, czemu coś zrobiłeś. Format: data + decyzja + powód.

## 2026-07-03 — Osobne repo zamiast folderu w kursie
**Decyzja:** Projekt jako samodzielne repo `Partner-Finder`, nie folder w repo kursu.
**Powód:** Wygląda profesjonalnie jako pierwszy „prawdziwy" projekt PM; czysty git od zera.

## 2026-07-03 — Backend Python + frontend czysty JS
**Decyzja:** Backend w Pythonie (FastAPI + OpenAI Agents SDK), frontend w czystym JS.
**Powód:** Rozdzielenie warstw = dorosła architektura; front i backend jako osobne epiki,
łatwe do prowadzenia niezależnie. Python bo tam jest logika AI; JS bo pełna kontrola nad UI/brandingiem.

## 2026-07-03 — Migracja z „ręcznego" OpenAI SDK na OpenAI Agents SDK
**Decyzja:** Przepisać logikę z `openai.chat.completions` na framework Agents SDK.
**Powód:** Nauka narzędzia branżowego; mniej boilerplate'u (pętla tool-calls, orkiestracja agentów).

## 2026-07-04 — Zakres: 2 tryby zamiast 1, wspólny silnik oceny
**Decyzja:** Produkt ma 2 tryby wejścia (Tryb 1: od URL → oceń + znajdź do 10 podobnych;
Tryb 2: od kryteriów miasto+województwo+branża → znajdź do 10 firm), ale **jeden wspólny
silnik oceny**. Pierwotne „tryby 1 i 2" (oba: znajdź podobne) scalone w jeden.
**Powód:** Oba dawne tryby robiły to samo (szukaj podobnych + oceń) — bez sensu dublować.
Rdzeń (scrape → scoring → zapis) jest wspólny; tryby różnią się tylko źródłem listy firm.

---

## Do rozstrzygnięcia (otwarte)

### Definicja „podobnej firmy" (Tryb 1)
Jak szukać firm „podobnych" do podanego URL? Ta sama branża? Region? Oba? — decyzja później.

### Faza 2 — które API do szukania partnerów?
Clutch i Google **nie pozwalają na zwykły scraping**. Opcje:
- **Google Places API** — dobre do Google Maps (firmy lokalne). Płatne po darmowym limicie.
- **SerpAPI** — wygodne wyniki Google/Maps jako JSON. Płatne (jest darmowy trial).
- **Google Custom Search API** — 100 zapytań/dzień za darmo, potem płatne.

➡️ Decyzja do podjęcia w Fazie 2 (kwestia budżetu — Twoja jako PM).
