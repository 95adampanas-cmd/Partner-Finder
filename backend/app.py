"""
Partner Finder — backend (FastAPI).

Opakowuje silnik oceny z main.ipynb w API, żeby dało się go odpalić w przeglądarce.
- POST /api/evaluate  {url}  -> ocena partnerska (tekst)
- /                          -> serwuje frontend (folder ../frontend)

Uruchomienie (z folderu backend/):
    uvicorn app:app --reload
Potem otwórz http://localhost:8000
"""

from pathlib import Path
from urllib.parse import urlparse
import csv
import uuid
import os

from dotenv import load_dotenv
from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
from agents import Agent, Runner, function_tool

# .env leży obok tego pliku (klucz OPENAI_API_KEY)
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)


# ── Narzędzia (tools) ─────────────────────────────────────────────────────────
@function_tool
def scrape_website(url: str) -> str:
    """Pobiera treść tekstową strony firmy (pierwsze 5000 znaków).

    Args:
        url: Adres strony do przeanalizowania, np. https://firma.pl
    """
    response = requests.get(url, timeout=20)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.get_text()[:5000]


@function_tool
def save_partner(company: str, url: str, score: int, reason: str) -> str:
    """Zapisuje dobrego partnera (score >= 7) do partners.csv.

    Args:
        company: Nazwa firmy.
        url: Adres strony firmy.
        score: Ocena dopasowania partnerskiego (1-10).
        reason: Uzasadnienie oceny.
    """
    with open("partners.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([company, url, score, reason])
    return "zapisano"


# budujemy 3 tool który odpali sobie model przy abalizie danego url w agent_score i agent_rerun ten tool ma pozwolic agentowi dostac się do dokuemntu values-categories,
# żeby zweryfikować synergie na pdostawie księgi wiedzy

@function_tool

def get_synergie() -> str:

    """Zwraca bazę wiedzy o synergiach i propozycji wartości dla partnerów (per kategoria).

     Wywołaj to narzędzie PO rozpoznaniu kategorii firmy, aby napisać KONKRETNĄ sekcję
    SYNERGIA dopasowaną do jej branży (nie ogólniki). Zwraca pełną treść dokumentu
    value-proposition.md: argumenty uniwersalne + synergie per kategoria
    (social media, webdev, marketing automation, branding, SEM, kreatywne, doradcze).
    """
    # wskazujemy sciezke do pliku z wiedzą value-proposition metodą path wskazujemy file i pobieramy go dzieki resolve
    text = Path(__file__).resolve().parent.parent / "docs" / "value-proposition.md"
    return text.read_text(encoding="utf-8")




# 4 tool który korzsysta z bazy outrech, gdzie zapisane są obiekcje itp i jak rozmawiać

@function_tool

def get_playbook() -> str:

    """Zwraca playbook zbijania obiekcji partnerów (per kategoria) z outreach-playbook.md.

    Wywołuj przy KAŻDEJ ocenie firmy — zawiera gotowe kontrargumenty na typowe obiekcje
    danej branży (np. webdev: "sami robimy SEO"; branding: "SEO zabije nasz tone of voice").
    Użyj tego, żeby w ocenie dodać sekcję JAK ROZMAWIAĆ / zbijanie obiekcji dla tej firmy.
    """
    sciezka = Path(__file__).resolve().parent.parent / "docs" / "outreach-playbook.md"
    return sciezka.read_text(encoding="utf-8")


# Zwykła funkcja (NIE @function_tool) — wołamy Tavily bezpośrednio z endpointu /api/similar.
def tavily_search(zapytanie: str, max_results: int = 15) -> list:
    key = os.environ.get("TAVILY_API_KEY") or os.environ.get("TVLY_API_KEY")
    if not key:
        return []
    client = TavilyClient(api_key=key)
    return client.search(zapytanie, max_results=max_results).get("results", [])


# Domeny/frazy katalogów, rankingów i agregatorów — odrzucamy je deterministycznie.
KATALOGI = (
    "clutch.co", "sortlist", "themanifest", "goodfirms", "designrush", "techbehemoths",
    "topcssgallery", "wikipedia", "facebook", "linkedin", "wordpress.org", "domenomania",
    "oferteo", "ceneo", "opineo", "youtube", "instagram",
    "/ranking", "najlepsze-", "top-10", "top10", "firm-i-agencji", "-agencji-ktore", "/blog/",
)


def filtruj_firmy(wyniki: list, wlasna_domena: str) -> list:
    """Zostawia realne firmy: usuwa katalogi/rankingi, ocenianą firmę i duplikaty domen."""
    firmy, widziane = [], set()
    for r in wyniki:
        url = r.get("url", "")
        dom = urlparse(url).netloc.replace("www.", "").lower()
        if not dom or dom in widziane:
            continue
        if wlasna_domena and wlasna_domena in dom:
            continue
        if any(k in url.lower() for k in KATALOGI):
            continue
        widziane.add(dom)
        firmy.append({"nazwa": (r.get("title") or dom)[:60], "url": url})
    return firmy[:10]



# ── Prompty ────────────────────────────────────────────────────────────────────
SCORING_INSTRUCTIONS = """Jesteś analitykiem partnerskim Last Agency - agencji SEO/SEM/GEO/AI Search z Poznania.
Wspierasz Growth & Partnerships Lead w budowie sieci partnerów: referral (polecają nam klientów) i white-label (zlecają nam usługi pod swoją marką).

ZADANIE: dostajesz URL firmy. Użyj scrape_website, oceń potencjał partnerski (1-10), i jeśli score >= 7, zapisz przez save_partner.

FLOW:
1. scrape_website na podanym URL
2. Rozpoznaj kategorię firmy i oceń wg kryteriów
3. Wywołaj get_synergie() i dopasuj synergię do rozpoznanej kategorii firmy
4. Wywołaj get_playbook() i dodaj sekcję JAK ROZMAWIAĆ (najczęstsze obiekcje tej branży + kontrargumenty)
5. Jeśli score >= 7 -> save_partner(company, url, score, reason)
6. Zwróć pełną ocenę

DOBRE KATEGORIE PARTNERÓW (firmy z tych obszarów = kandydaci na referral/white-label):
- Web dev / software house / twórcy sklepów (zwł. e-commerce)
- Agencje e-commerce (wdrożenia PrestaShop/Magento/Shopify/headless)
- Agencje brandingowe, kreatywne, social media
- Marketing automation (resellerzy/twórcy narzędzi)
- Digital advisory & delivery (doradztwo e-commerce, analityka, PM)
- Integratory CRM/ERP/PIM, CMS/SaaS e-commerce
- Kancelarie prawne e-commerce/RODO/AI
- Agencje AI/automatyzacje/chatboty, narzędzia GEO/AI-visibility
- Agencje growth/consulting, HR/employer branding, CRO
- Persony: doradcy biznesowi, dyrektorzy sprzedaży/marketingu, prawnicy e-commerce, osoby z siecią kontaktów

MOCNE SYGNAŁY (podbijają score do 8-10 - NIE asekuruj się szóstką jeśli je widzisz):
- E-commerce na premium platformach (PrestaShop, Magento, Shopify Plus) -> klienci z budżetem
- Oficjalny partner platformy (PrestaShop 3 gwiazdki, Shopify Partner) -> wiarygodność, top tier
- Dział marketingu / rozbudowana oferta -> gotowość na referral (wspólne migracje, prowizja = dodatkowe MRR)
- Naturalna synergia e-commerce <-> SEO: ich klienci (sklepy) potrzebują SEO/SEM
- Lider niszy / dużo case studies / wielu klientów -> skala i wolumen

PRZYKŁAD-KOTWICA:
Firma jak Tebim (sklepy PrestaShop, partner 3 gwiazdki, e-commerce, dział marketingu, top 3 w niszy) = score 9, model referral. Widzisz podobny profil -> oceniaj 8-10, nie 6.

ZŁY PARTNER (score 1-4):
- Agencja SEO/SEM/GEO/pozycjonowanie - bezpośredni konkurent
- Full-service 360 z własnym działem SEO
- Katalog/portal/agregator (Clutch, Sortlist)
- Freelancer bez klientów, firma spoza Polski
- Globalny gigant poza naszą skalą (np. worldline)

ŚREDNI (5-6): za mało danych/budżetu LUB realnie prowadzi SEO jako jedną z głównych usług.

WAŻNE — jak traktować sygnały SEO/SEM/GEO u firmy (NIE zaniżaj pochopnie):
- Rozróżnij OFERTĘ RDZENIOWĄ od WZMIANKI POBOCZNEJ. Pojedyncze słowo w formularzu kontaktowym,
  menu czy liście wyboru (np. opcja "Pozycjonowanie") to NIE dowód, że firma świadczy usługę SEO.
  NIE zakładaj pełnego SEO in-house na podstawie jednej wzmianki.
- Jeśli firma ma odrobinę SEO, ale jej RDZEŃ to co innego (e-commerce, webdev, branding...) →
  traktuj jako SUB-PARTNERA / częściowego konkurenta w SEO, a NIE blokera. To NIE obniża score
  mocnego partnera e-commerce — nadal może być 8-9.
- Pełny KONKURENT (niski score) = firma, której GŁÓWNA, eksponowana oferta to SEO/SEM/GEO/pozycjonowanie.
- Widzisz tylko stronę główną (pierwsze 5000 znaków) — jeśli nie masz pewności co do zakresu SEO,
  załóż korzystnie dla partnera e-commerce i zaznacz niepewność, zamiast tankować score.

KRYTERIA KWALIFIKACJI:
- Brak konkurencyjnego SEO/SEM/GEO in-house (chyba że jako sub-partner)
- Portfolio klientów pasujące do profilu Last Agency
- Potencjał wolumenu (liczba klientów, częstotliwość projektów)
- Wiarygodność (opinie, lata działania, referencje)

SYNERGIA / PROPOZYCJA WARTOŚCI:
Aby napisać sekcję SYNERGIA, WYWOŁAJ narzędzie get_synergie() — zwraca pełną bazę wiedzy
(argumenty uniwersalne + synergie per kategoria). Wybierz część pasującą do rozpoznanej
kategorii firmy i podaj 3-4 KONKRETNE argumenty (konkrety z bazy, nie ogólniki).

W OCENIE ZAWRZYJ:
- score (1-10) + czy kontaktować (TAK/NIE)
- SYNERGIA: 3-4 konkretne argumenty, DLACZEGO ta firma zyska na partnerstwie (dopasowane do jej kategorii)
- JAK ROZMAWIAĆ: 2-3 najczęstsze obiekcje tej branży + krótki kontrargument na każdą (z get_playbook)
- kategoria firmy (z listy powyżej)
- rekomendowany model: referral / white-label / oba
- czy mają SEO/SEM/GEO w ofercie (jeśli tak: konkurent czy sub-partner)
- szacowany profil klientów (wielkość, budżety)
- dane kontaktowe JEŚLI są na stronie (telefon, mail) - NIE zmyślaj, podaj tylko to, co faktycznie znalazłeś
- 3 zdania uzasadnienia oparte na treści strony

TON: konkretnie, bez lania wody, bez zbędnych disclaimerów."""

EVALUATOR_PROMPT = """Oceniasz JAKOŚĆ analizy partnerskiej wykonanej przez innego agenta AI dla Last Agency - agencji SEO/SEM/GEO z Poznania. NIE oceniasz firmy od nowa - sprawdzasz, czy ocena agenta jest solidna i zgodna z kryteriami.

CO SPRAWDZASZ:
1. Czy score jest poparty KONKRETNYMI faktami ze strony (nazwa usług, platformy, klienci), a nie ogólnikami.
2. Czy agent poprawnie ocenił sygnały SEO/SEM/GEO:
   - KONKURENT = firma, której GŁÓWNA, eksponowana oferta to SEO/SEM/GEO. Wysoki score dla takiego -> BŁĄD.
   - ALE pojedyncza wzmianka (słowo w formularzu/menu, np. "Pozycjonowanie") NIE czyni firmy konkurentem.
     Jeśli agent ZANIŻYŁ score mocnego partnera e-commerce z powodu pobocznej wzmianki SEO -> BŁĄD, każ PODNIEŚĆ.
   - Firma z odrobiną SEO, ale rdzeniem gdzie indziej (e-commerce, webdev) = sub-partner, nie bloker.
3. Czy agent NIE ZANIŻYŁ score przy widocznych MOCNYCH SYGNAŁACH. To częsty błąd - asekurowanie się szóstką.
   MOCNE SYGNAŁY, które powinny dać 8-10:
   - e-commerce na premium platformach (PrestaShop, Magento, Shopify Plus)
   - oficjalny partner platformy (np. PrestaShop 3 gwiazdki, Shopify Partner)
   - dział marketingu / rozbudowana oferta wdrożeniowa
   - naturalna synergia e-commerce <-> SEO, wielu klientów, lider niszy
   (Wzorzec: firma jak Tebim = 9. Jeśli agent widział taki profil i dał 6 -> BŁĄD, każ podnieść.)
4. Czy rekomendowany model (referral / white-label / oba) ma sens dla tej firmy.
5. Czy agent NIE ZMYŚLIŁ danych kontaktowych - kontakt (telefon/mail) jest OK tylko jeśli faktycznie był na stronie.
6. Czy uzasadnienie odnosi się do treści strony, a nie do ogólnych założeń.

ODRZUĆ (is_acceptable: false), jeśli:
- score 7+ dla konkurenta SEO/SEM/GEO (bez zaznaczenia "sub-partner")
- score zaniżony mimo wyraźnych mocnych sygnałów (np. premium e-commerce z partnerstwem platformy dostaje 6)
- uzasadnienie bez konkretów ze strony
- score 7+ dla firmy spoza Polski lub agregatora/katalogu
- zmyślone dane kontaktowe
- brak wskazania modelu współpracy przy wysokim score

ZATWIERDŹ (is_acceptable: true), jeśli:
- score wynika z konkretnych faktów ze strony
- poprawnie rozpoznano konkurenta vs partnera
- mocne sygnały właściwie zważone (nie zaniżone)
- uzasadnienie spójne ze score

W polu feedback napisz KONKRETNIE co jest nie tak i jak poprawić (np. "firma jest partnerem PrestaShop 3 gwiazdki - to mocny sygnał, score powinien być 8-9, nie 6"). Jeśli wszystko OK, feedback krótki: "ocena solidna".

TON: konkretnie, bez lania wody."""


# ── Model odpowiedzi evaluatora ───────────────────────────────────────────────
class Evaluator(BaseModel):
    is_acceptable: bool
    feedback: str


# ── Agenci ─────────────────────────────────────────────────────────────────────
MODEL = "gpt-5.4-nano"

agent = Agent(
    name="Partner Finder",
    instructions=SCORING_INSTRUCTIONS,
    tools=[scrape_website, save_partner, get_synergie, get_playbook],
    model=MODEL,
)

agent_evaluator = Agent(
    name="evaluate",
    instructions=EVALUATOR_PROMPT,
    output_type=Evaluator,
    model=MODEL,
)

agent_rerun = Agent(
    name="rerun",
    instructions=SCORING_INSTRUCTIONS
    + "\n\nDODATKOWO: dostajesz FEEDBACK od weryfikatora do swojej poprzedniej oceny. Uwzględnij go i oceń ponownie, bardziej precyzyjnie.",
    tools=[scrape_website, save_partner, get_synergie, get_playbook],
    model=MODEL,
)


# ── Czat / asystent researchu ───────────────────────────────────────────────
# Agent czatowy: kontynuuje rozmowę o ocenionej firmie (research + outreach).
CHAT_INSTRUCTIONS = SCORING_INSTRUCTIONS + """

TRYB CZATU: Firma została już oceniona (ocena jest w historii rozmowy powyżej).
Teraz odpowiadasz na pytania uzupełniające Growth & Partnerships Leada — pomagasz w
researchu i przygotowaniu do rozmowy z partnerem. Korzystaj z kontekstu oceny oraz z
narzędzi: get_synergie (baza synergii per kategoria) i get_playbook (zbijanie obiekcji).
Bądź konkretny, bez lania wody. NIE oceniaj firmy od nowa i NIE zapisuj niczego — po prostu
pomagaj (argumenty, synergie, drafty wiadomości, angle kontaktu, kontrargumenty, porównania).
Odpowiadaj po polsku.
"""

agent_chat = Agent(
    name="chat",
    instructions=CHAT_INSTRUCTIONS,
    tools=[get_synergie, get_playbook],
    model=MODEL,
)


# ── Wyszukiwanie podobnych firm (Tavily) ──
# Agent robi TYLKO jedną prostą rzecz: generuje zapytanie do wyszukiwarki (nano wystarczy).
# Wywołanie Tavily i filtrowanie robi deterministyczny kod w /api/similar (pewne, powtarzalne).
agent_query = Agent(
    name="query",
    instructions="""Na podstawie oceny firmy z historii: napisz JEDNO krótkie zapytanie do wyszukiwarki
(po polsku), które znajdzie REALNE firmy z tej samej branży/kategorii w Polsce (podobne agencje/firmy).
Używaj fraz USŁUGOWYCH (np. "tworzenie stron WordPress", "agencja e-commerce PrestaShop", "software house Poznań"),
a NIE fraz typu "ranking / top 10 / najlepsze firmy". Zwróć TYLKO samo zapytanie, bez cudzysłowów i komentarza.""",
    model=MODEL,
)


# Pamięć rozmów: conversation_id -> historia wiadomości.
# UWAGA: w RAM (efemeryczne) — znika przy restarcie serwera. Na MVP wystarcza.
sesje: dict[str, list] = {}


# ── Orkiestracja (jak w notebooku) ─────────────────────────────────────────────
async def evaluator(url: str, reply: str) -> Evaluator:
    kontekst = f"Zapytanie (URL): {url}\n\nOcena agenta do weryfikacji:\n{reply}"
    result = await Runner.run(agent_evaluator, kontekst)
    return result.final_output


async def rerun(url: str, feedback: str) -> str:
    poprawka = (
        f"Poprzednia ocena {url} została odrzucona.\n"
        f"FEEDBACK: {feedback}\n"
        f"Oceń ponownie, uwzględniając feedback. URL: {url}"
    )
    result = await Runner.run(agent_rerun, poprawka)
    return result.final_output


async def evaluate_company(url: str) -> str:
    result = await Runner.run(agent, url)
    reply = result.final_output

    verdict = await evaluator(url, reply)
    if verdict.is_acceptable:
        return reply
    return await rerun(url, verdict.feedback)


# ── API (Starlette) ───────────────────────────────────────────────────────────
async def api_evaluate(request):
    try:
        body = await request.json()
        url = (body.get("url") or "").strip()
        if not url:
            return JSONResponse({"ok": False, "error": "Brak URL"})
        wynik = await evaluate_company(url)
        # Zakładamy sesję czatu: zaczynamy historię od zapytania i gotowej oceny.
        cid = str(uuid.uuid4())
        sesje[cid] = [
            {"role": "user", "content": f"Oceń firmę: {url}"},
            {"role": "assistant", "content": wynik},
        ]
        return JSONResponse({"ok": True, "result": wynik, "conversation_id": cid})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})


async def api_chat(request):
    try:
        body = await request.json()
        cid = body.get("conversation_id")
        message = (body.get("message") or "").strip()
        if not message:
            return JSONResponse({"ok": False, "error": "Pusta wiadomość"})
        historia = sesje.get(cid)
        if historia is None:
            return JSONResponse({"ok": False, "error": "Sesja wygasła — oceń firmę ponownie."})
        # dopisujemy pytanie usera i odpalamy agenta czatowego z całą historią
        historia.append({"role": "user", "content": message})
        result = await Runner.run(agent_chat, historia)
        sesje[cid] = result.to_input_list()  # zapisujemy zaktualizowaną historię
        return JSONResponse({"ok": True, "reply": result.final_output})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})


async def api_similar(request):
    try:
        body = await request.json()
        cid = body.get("conversation_id")
        historia = sesje.get(cid)
        if historia is None:
            return JSONResponse({"ok": False, "error": "Sesja wygasła — oceń firmę ponownie."})

        # 1) LLM generuje TYLKO zapytanie (proste, pewne)
        r = await Runner.run(agent_query, historia + [{"role": "user", "content": "Podaj zapytanie do wyszukiwarki."}])
        zapytanie = (r.final_output or "").strip().strip('"')

        # 2) własna domena ocenianej firmy (żeby ją odfiltrować)
        wlasny_url = ""
        for m in historia:
            c = m.get("content", "") if isinstance(m, dict) else ""
            if isinstance(c, str) and "Oceń firmę:" in c:
                wlasny_url = c.split("Oceń firmę:")[-1].strip()
                break
        wlasna_domena = urlparse(wlasny_url).netloc.replace("www.", "").lower() if wlasny_url else ""

        # 3) Tavily + deterministyczny filtr
        wyniki = tavily_search(zapytanie, max_results=15)
        firmy = filtruj_firmy(wyniki, wlasna_domena)
        return JSONResponse({"ok": True, "companies": firmy, "zapytanie": zapytanie})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})


# Frontend serwowany pod / (Mount MUSI być po trasach /api)
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

app = Starlette(routes=[
    Route("/api/evaluate", api_evaluate, methods=["POST"]),
    Route("/api/chat", api_chat, methods=["POST"]),
    Route("/api/similar", api_similar, methods=["POST"]),
    Mount("/", app=StaticFiles(directory=str(frontend_dir), html=True), name="frontend"),
])
