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
import csv

from dotenv import load_dotenv
from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles
import requests
from bs4 import BeautifulSoup
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


# ── Prompty ────────────────────────────────────────────────────────────────────
SCORING_INSTRUCTIONS = """Jesteś analitykiem partnerskim Last Agency - agencji SEO/SEM/GEO/AI Search z Poznania.
Wspierasz Growth & Partnerships Lead w budowie sieci partnerów: referral (polecają nam klientów) i white-label (zlecają nam usługi pod swoją marką).

ZADANIE: dostajesz URL firmy. Użyj scrape_website, oceń potencjał partnerski (1-10), i jeśli score >= 7, zapisz przez save_partner.

FLOW:
1. scrape_website na podanym URL
2. Rozpoznaj kategorię firmy i oceń wg kryteriów
3. Jeśli score >= 7 -> save_partner(company, url, score, reason)
4. Zwróć pełną ocenę

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

ŚREDNI (5-6): ma klientów, ale trochę SEO w ofercie (ryzyko konfliktu) LUB za mało danych/budżetu.
Uwaga: firma z SEO in-house NIE zawsze jest zła - może być sub-partnerem. Zaznacz to.

KRYTERIA KWALIFIKACJI:
- Brak konkurencyjnego SEO/SEM/GEO in-house (chyba że jako sub-partner)
- Portfolio klientów pasujące do profilu Last Agency
- Potencjał wolumenu (liczba klientów, częstotliwość projektów)
- Wiarygodność (opinie, lata działania, referencje)

SYNERGIA / PROPOZYCJA WARTOŚCI (dopasuj do kategorii firmy — WSKAŻ, dlaczego TA firma zyska na partnerstwie):
Argumenty uniwersalne (dla każdej firmy):
- Budowanie MRR/LTV: referral/white-label = powtarzalny przychód, klient zostaje dłużej.
- Prowizja, która ucieka: brak polecenia = utracony przychód (zgarnie go ktoś inny).
- Cementowanie relacji: dokładając brakującą usługę pod ich marką, partner mocniej wiąże klienta.
- Bezpieczny partner: nie zabieramy klienta, oddajemy z powrotem (inaczej niż agencja 360).
- Nowy kanał GEO/AI Search pod ich marką (klienci pytają o AI Overviews / ChatGPT Search).
Per kategoria (użyj pasującej do rozpoznanej branży):
- Social media: GEO/AI Search pod marką; wymiana danych (keywordy z Google <-> insighty social -> lepsze stawki SEM); domykanie lejka po reklamie na FB.
- Webdev/software house: backlog zadań technicznych = płatne godziny dla nich (upselling); ochrona przed "ładną, ale martwą stroną"; bezpieczne migracje (301, ochrona ruchu).
- Marketing automation: kaloryczny ruch -> szybszy wzrost bazy -> upselling wyższego planu; ratowanie retencji (narzędzie ma na czym pracować); my przed kliknięciem, oni po.
- Agencje brandingowe: mierzalny ROI rebrandingu (ruch w GA4); ochrona przy zmianie domeny (audyt SEO); ochrona Brand SERP; projekt jednorazowy -> stały przychód.
- Agencje SEM (tylko płatne, bez SEO in-house = KOMPLEMENTARNY partner, NIE konkurent): klauzula Non-Compete; niższy CPC przez Quality Score; wymiana danych o frazach.
- Agencje kreatywne: przedłużenie życia kampanii "burst" (przechwytujemy intencję); upselling produkcji (wideo/infografiki pod SGE); praca w warstwie niewidocznej - nie tykamy kreacji.
- Firmy doradcze/konsulting: wiarygodne ramię egzekucyjne (zaufany wykonawca strategii); dwukierunkowy cross-selling leadów; wspólne KPI i raportowanie do zarządu.

W OCENIE ZAWRZYJ:
- score (1-10) + czy kontaktować (TAK/NIE)
- SYNERGIA: 1-2 konkretne argumenty, DLACZEGO ta firma zyska na partnerstwie (dopasowane do jej kategorii)
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
2. Czy agent poprawnie rozpoznał, czy firma ma SEO/SEM/GEO w ofercie:
   - jeśli ma i dostała wysoki score jako "partner" (nie sub-partner) -> BŁĄD, to konkurent.
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
MODEL = "gpt-5.4-mini"

agent = Agent(
    name="Partner Finder",
    instructions=SCORING_INSTRUCTIONS,
    tools=[scrape_website, save_partner],
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
    tools=[scrape_website, save_partner],
    model=MODEL,
)


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
        return JSONResponse({"ok": True, "result": wynik})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})


# Frontend serwowany pod / (Mount MUSI być po trasach /api)
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

app = Starlette(routes=[
    Route("/api/evaluate", api_evaluate, methods=["POST"]),
    Mount("/", app=StaticFiles(directory=str(frontend_dir), html=True), name="frontend"),
])
