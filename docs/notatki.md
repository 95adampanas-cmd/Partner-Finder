Co jest „tool", a co NIE
Tool = coś, czego AI samo NIE umie i musi „wyjść na zewnątrz":

pobrać stronę z internetu 🌐
zapisać plik 💾
wyszukać coś w Google 🔍
NIE-tool = coś, co AI robi samo (myślenie na podstawie tekstu):

ocena/scoring — model czyta tekst strony i sam wystawia score. To nie narzędzie, to „mózg" agenta.
wyciągnięcie branży ze strony — model to wywnioskuje z treści.
decyzja „dobry/zły partner".
To ważne, bo na początku łatwo pomyśleć „potrzebuję narzędzia do oceniania" — a nie, ocenianie to sam agent.

Pełna lista narzędzi w projekcie
Tool	Co robi	Kiedy
scrape_website	pobiera treść strony firmy	Faza 1 — piszesz teraz ✅
save_partner	zapisuje dobrych partnerów	Faza 1 — zaraz
search_companies	znajduje firmy (Google/Maps/Clutch)	Faza 2
To wszystko. Trzy narzędzia na cały produkt. Reszta to praca agentów (patrz niżej).

A „agenci"? (to nie narzędzia)
W projekcie są 2 agenci — to osobna kategoria niż tools:

Agent oceniający — używa narzędzi (scrape, search, save) i wystawia score
Agent evaluator — sprawdza jakość oceny (druga para oczu)
Jak to się składa w 2 tryby (Faza 2)

TRYB 1 (od URL):
  scrape_website(url) → agent wyciąga branżę → search_companies(branża)
  → dla każdej: scrape + ocena → save_partner (dobrych)

TRYB 2 (od kryteriów):
  search_companies(miasto+województwo+branża)
  → dla każdej: scrape + ocena → save_partner (dobrych)
Widzisz? Te same 3 narzędzia w obu trybach, tylko inaczej poukładane. Dlatego mówiłem „jeden silnik, dwa wejścia".
