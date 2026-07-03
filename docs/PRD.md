# PRD — Partner Finder

> Product Requirements Document. Odpowiada na pytanie: **co budujemy i po co.**
> Właściciel: PM (Adam). Aktualizuj, gdy zmienia się zakres.

## 1. Problem

Last Agency (SEO/SEM/GEO/AI Search, Poznań) chce pozyskiwać **firmy partnerskie** —
agencje digital, które mają własnych klientów, ale **nie robią SEO/SEM**, więc mogą
nasze usługi odsprzedawać (white-label) lub polecać za prowizję (referral).

Ręczne szukanie i ocenianie takich firm jest wolne. Chcemy to zautomatyzować.

## 2. Cel produktu

Narzędzie, które:
1. Dostaje URL firmy → ocenia jej potencjał partnerski (score 1–10 + uzasadnienie).
2. Znajduje **podobne** firmy-partnerów w sieci (Google / Clutch / Google Maps).
3. Zapisuje dobrych partnerów (score ≥ 7) do bazy.
4. Jest dostępne przez prostą stronę web z brandingiem Last Agency.

## 3. Użytkownik

- **Główny:** PM / sprzedaż w Last Agency — wkleja URL, dostaje ocenę i listę leadów.

## 4. Zakres (MVP)

**W zakresie:**
- Ocena pojedynczej firmy po URL (agent + tool scrapujący stronę).
- Evaluator sprawdzający jakość oceny (druga para oczu AI).
- Zapis dobrych partnerów do CSV.
- Tool: szukanie podobnych firm.
- Frontend web: pole na URL → wynik oceny.

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
