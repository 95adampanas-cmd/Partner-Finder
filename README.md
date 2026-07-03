# Partner Finder

Narzędzie AI dla **Last Agency** (agencja SEO/SEM/GEO/AI Search z Poznania), które:

1. **Ocenia** firmy pod kątem potencjału partnerskiego (na podstawie ich strony www),
2. **Szuka** podobnych firm-partnerów (Google / Clutch / Google Maps),
3. Udostępnia to przez **stronę web** z brandingiem Last Agency.

## Architektura

```
Frontend (czysty HTML/CSS/JS)        Backend (Python)
  UI + branding            →  FastAPI  →  OpenAI Agents SDK
  wysyła URL, pokazuje wynik  ←  (REST)  ←  agenci + tools
```

- **backend/** — Python, FastAPI, OpenAI Agents SDK (logika + API)
- **frontend/** — czysty JavaScript (UI)
- **docs/** — dokumentacja projektu prowadzonego jako PM

## Szybki start (backend)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # i wpisz swój OPENAI_API_KEY
uvicorn app:app --reload
```

## Dokumentacja

Projekt prowadzony jako pierwszy projekt PM — patrz [docs/](docs/):
- [PRD.md](docs/PRD.md) — co budujemy i po co
- [ROADMAP.md](docs/ROADMAP.md) — fazy i status
- [DECISIONS.md](docs/DECISIONS.md) — log decyzji
- [BRAND.md](docs/BRAND.md) — identyfikacja wizualna
