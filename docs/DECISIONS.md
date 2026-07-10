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

## 2026-07-10 — Search API: Tavily zamiast Custom Search + scoring na żądanie
**Decyzja:** Do wyszukiwania podobnych firm używamy **Tavily** (`tavily-python`), nie Google Custom Search.
UX: przycisk „🔍 Znajdź 10 podobnych" znajduje firmy (nazwa+URL) BEZ scoringu; każda domena ma guzik
**[Oceń]**, który uruchamia pełny scoring TYLKO dla niej (reużywa `/api/evaluate`). Szukanie manualne
(nie auto po URL) — kontrola kosztów.
**Powód:** Tavily jest zbudowane dla agentów AI (czyste wyniki, prosty SDK, jeden klucz `TAVILY_API_KEY`,
free ~1000/mies). Wzorzec „szukaj tanio, oceniaj na żądanie" (pomysł Adama) rozwiązuje koszt/czas —
nie oceniamy 10 firm na ślepo, tylko wybrane na klik.
**Jak:** narzędzie `szukaj_firm` (Tavily) → `agent_search` (output_type=PodobneFirmy) generuje zapytanie
z kontekstu oceny (sesja) i zwraca listę → endpoint `/api/similar` → frontend renderuje listę z guzikami [Oceń].

## 2026-07-10 — Sygnał SEO ≠ automatyczny konkurent (sub-partner, nie bloker)
**Decyzja:** Firma z odrobiną SEO, ale rdzeniem gdzie indziej (e-commerce, webdev...) = **sub-partner /
częściowy konkurent**, NIE bloker partnerstwa. Nie obniża score mocnego partnera e-commerce (może być 8-9).
Rozróżniamy **ofertę rdzeniową** od **wzmianki pobocznej** (słowo w formularzu/menu ≠ realna usługa SEO).
Pełny konkurent (niski score) = firma, której GŁÓWNA oferta to SEO/SEM/GEO.
**Powód:** Agent zaniżał Tebim (mocny partner PrestaShop/e-commerce) do 6-8, bo z opcji „Pozycjonowanie"
w formularzu wnioskował „konkurent SEO". Adam zweryfikował: Tebim NIE oferuje SEO. Skrap widzi tylko
stronę główną (5000 znaków), więc łatwo o nadinterpretację. Zakodowane w SCORING_INSTRUCTIONS + EVALUATOR_PROMPT.

## 2026-07-09 — Search API: Google Custom Search na start
**Decyzja:** Do wyszukiwania firm (Faza 2) używamy **Google Custom Search API**.
Places API (dane kontaktowe firm z Map) dołożymy później, gdy przepływ zadziała.
**Powód:** 100 zapytań/dzień za darmo (nauka bez kosztów), zwraca linki webowe, które
wpinają się w istniejący `scrape_website` + scoring. Zero ryzyka budżetowego na start.
**Jak obsługuje 2 tryby:** jedno narzędzie `search_companies(zapytanie)`; różni się tylko
źródło zapytania — Tryb 2: user (miasto+branża), Tryb 1: agent buduje z profilu wyczytanego z URL-a.
Rozwiązuje też open question „co znaczy podobna firma" (= ta sama branża, wyciągnięta przez agenta).

## 2026-07-04 — Zakres: 2 tryby zamiast 1, wspólny silnik oceny
**Decyzja:** Produkt ma 2 tryby wejścia (Tryb 1: od URL → oceń + znajdź do 10 podobnych;
Tryb 2: od kryteriów miasto+województwo+branża → znajdź do 10 firm), ale **jeden wspólny
silnik oceny**. Pierwotne „tryby 1 i 2" (oba: znajdź podobne) scalone w jeden.
**Powód:** Oba dawne tryby robiły to samo (szukaj podobnych + oceń) — bez sensu dublować.
Rdzeń (scrape → scoring → zapis) jest wspólny; tryby różnią się tylko źródłem listy firm.

---

## Do rozstrzygnięcia (otwarte)

### Kto wyzwala zapis partnera — agent czy user?
W wersji CLI (Faza 1) **agent** sam zapisuje partnerów ze score ≥ 7 przez `save_partner`.
W wersji z frontem (Faza 3) alternatywa: to **user klika „Zapisz lead"** na ekranie
(więcej kontroli). Do rozstrzygnięcia przy budowie frontu.

### Definicja „podobnej firmy" (Tryb 1)
Jak szukać firm „podobnych" do podanego URL? Ta sama branża? Region? Oba? — decyzja później.

### Rozszerzenie zakresu: zbieranie kontaktów + output jako tabela (Faza 2/3)
Docelowa wizja (z metodologii Growth & Partnerships Lead) chce dla każdej firmy:
telefon, mail, LinkedIn osoby decyzyjnej oraz output jako **tabelę do arkusza**
(Nazwa | Kategoria | Miasto | Województwo | Telefon | Mail | LinkedIn | Model | Uzasadnienie).
- Telefon/mail często SĄ na stronie → agent może je wyciągnąć ze scrape (częściowo działa już dziś).
- LinkedIn osoby decyzyjnej + pewne dane kontaktowe → wymaga **nowych narzędzi** (search / LinkedIn) → Faza 2/3.
- Pomysł na tool `check_financials` (bizraport.pl / KRS) → weryfikacja skali/liczby klientów (poza stroną).
➡️ Na razie: agent podaje kontakt TYLKO jeśli jest na scrapowanej stronie i NIE zmyśla.
   Pełna tabela + LinkedIn + financials — po dołożeniu narzędzi.

### Faza 2 — które API do szukania partnerów?
Clutch i Google **nie pozwalają na zwykły scraping**. Opcje:
- **Google Places API** — dobre do Google Maps (firmy lokalne). Płatne po darmowym limicie.
- **SerpAPI** — wygodne wyniki Google/Maps jako JSON. Płatne (jest darmowy trial).
- **Google Custom Search API** — 100 zapytań/dzień za darmo, potem płatne.

➡️ Decyzja do podjęcia w Fazie 2 (kwestia budżetu — Twoja jako PM).
