# Search Methodology — jak szukać firm (Faza 2)

> Metodologia geograficznego researchu partnerów. Źródło: Growth & Partnerships Lead.
> Zastosowanie: logika narzędzia `search_companies` i orkiestracja **Trybu 2** (Faza 2).
> DZIŚ agent tego NIE robi (brak narzędzia szukającego) — to plan na Fazę 2.

## Zasada: pokrycie całej Polski, nie tylko duże miasta

Szukaj systematycznie, region po regionie — małe i średnie miasta (20–100 tys.) często mają
lokalne software house'y, agencje i sklepy e-commerce **bez własnego SEO**, łatwiejsze do
domknięcia jako partner.

## Kolejność researchu

1. **Województwo po województwie** — wszystkie 16, nie pomijaj żadnego.
2. W każdym województwie: **miasta wojewódzkie → miasta powiatowe → mniejsze miejscowości/gminy**.
3. Nie ograniczaj się do Warszawy / Krakowa / Poznania / Wrocławia.
4. **Osobne zapytania per region**, nie jedno ogólne na cały kraj. Przykłady:
   - „software house Rzeszów"
   - „agencja marketingowa Radom"
   - „sklep internetowy producent Krosno"
5. **Iteracyjnie** — od największych ośrodków w województwie schodzimy niżej, aż wyczerpiemy
   sensowną pulę (nie szukamy agencji SEO we wsi 300 osób, ale lokalny sklep e-commerce/producent
   — jak najbardziej).

## Raportowanie postępu

Raportuj pokrycie **per województwo**, żeby PM widział status. Przykład:

> woj. podkarpackie — sprawdzone: Rzeszów, Krosno, Przemyśl, Mielec; do zrobienia: reszta powiatów.

## Implikacja techniczna (Faza 2)

- Wymaga narzędzia `search_companies(zapytanie / miasto+województwo+branża)` opartego o
  Google Places / SerpAPI / Custom Search (decyzja o API — patrz DECISIONS.md).
- Tryb 2 = pętla po regionach + kategoriach, z zapisem postępu.
