# PRD — Partner Finder

> Product Requirements Document. Odpowiada na pytanie: **co budujemy i po co.**
> Właściciel: PM (Adam). Aktualizuj, gdy zmienia się zakres.

## 1. Problem

Last Agency (SEO/SEM/GEO/AI Search, Poznań) chce pozyskiwać **firmy partnerskie** —
agencje digital, które mają własnych klientów, ale **nie robią SEO/SEM**, więc mogą
nasze usługi odsprzedawać (white-label) lub polecać za prowizję (referral).

Ręczne szukanie i ocenianie takich firm jest wolne. Chcemy to zautomatyzować.

## 2. Cel produktu

Narzędzie działa w **2 trybach**, ale ma **jeden wspólny silnik oceny**
(scrape strony → scoring 1–10 + uzasadnienie → zapis dobrych partnerów).
Tryby różnią się tylko tym, **skąd biorą listę firm do oceny**:

- **Tryb 1 — od firmy:** podajesz URL firmy → (opcjonalnie oceniamy ją) i znajdujemy
  do **10 podobnych** firm, oceniając każdą.
- **Tryb 2 — od kryteriów:** podajesz **miasto + województwo + branżę** → znajdujemy
  do **10 firm** pasujących do kryteriów i oceniamy każdą.

Dobrzy partnerzy (score ≥ 7) trafiają do bazy (CSV). Całość dostępna przez stronę web z brandingiem Last Agency.

## 3. Użytkownik

- **Główny:** PM / sprzedaż w Last Agency — podaje firmę **lub** kryteria (miasto/branża),
  dostaje listę ocenionych leadów partnerskich.

## 4. Zakres (MVP)

**Wspólny silnik oceny (rdzeń):**
- Tool `scrape_website` — pobiera treść strony firmy.
- Agent oceniający — scoring 1–10 + uzasadnienie wg kryteriów (sekcja 5).
- Evaluator — druga para oczu AI, sprawdza jakość oceny.
- Tool `save_partner` — zapis dobrych partnerów (score ≥ 7) do CSV.

**Trzy „wejścia" produkujące listę firm do oceny:**
- Tryb 1: z URL → znajdź do 10 podobnych (definicja „podobne" — TBD, patrz niżej).
- Tryb 2: z miasta + województwa + branży → znajdź do 10 firm.
- Tool wyszukujący firmy (Google / Clutch / Google Maps — API do wyboru, patrz DECISIONS.md).

**Frontend web:** wybór trybu → formularz → lista ocenionych firm.

**⚠️ Do doprecyzowania (open questions):**
- Definicja „podobnej firmy" w trybie 1 (ta sama branża? region? oba?) — decyzja później.

**Poza zakresem (na razie):**
- Logowanie/konta użytkowników.
- Baza danych (na start CSV wystarczy).
- Automatyczny mailing do partnerów.

## 5. Kryteria partnera (logika oceny)

**Dobry (7–10):** polska agencja digital bez SEO/SEM w ofercie (web dev, UX/UI,
branding, social, PR, e-commerce), z własnymi klientami B2B, pasuje do white-label lub referral.

**Zły (1–4):** agencja SEO/SEM (konkurent), full-service 360 z własnym SEO, katalog/portal
(Clutch, Sortlist), freelancer bez klientów, firma spoza Polski.

**Średni (5–6):** ma klientów, ale trochę SEO w ofercie; mała firma bez pewności budżetu.

## 6. Metryka sukcesu

- Trafność oceny (czy PM zgadza się ze scoringiem) — cel: >80% ocen „sensownych".
- Liczba znalezionych realnych leadów partnerskich na 1 zapytanie.
