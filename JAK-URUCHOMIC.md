# Jak uruchomić Partner Finder 🚀

Aplikacja ma **dwie części, które muszą działać razem:**
- **Backend** (serwer Python) — „mózg": agenci AI, OpenAI
- **Frontend** (strona w przeglądarce) — „twarz": pole na URL i wynik

⚠️ **Frontend BEZ backendu nie zadziała** (zobaczysz `NetworkError`).
Nigdy nie otwieraj `index.html` podwójnym klikiem — zawsze przez serwer i adres `localhost`.

---

## Uruchomienie — krok po kroku

### 1. Otwórz terminal w folderze `backend`
W Cursorze: terminal → wejdź do folderu backend:
```
cd Partner-Finder/backend
```

### 2. (Pierwszy raz) zainstaluj biblioteki
```
pip install -r requirements.txt
```
Tylko za pierwszym razem albo po zmianie `requirements.txt`.

### 3. Sprawdź, że masz klucz w `.env`
W `backend/.env` musi być:
```
OPENAI_API_KEY=sk-...
```
(plik jest w `.gitignore`, nie trafia na GitHub)

### 4. Odpal serwer
```
uvicorn app:app --reload
```
Zobaczysz coś w stylu `Uvicorn running on http://127.0.0.1:8000`.
**Zostaw ten terminal otwarty** — serwer musi chodzić przez cały czas używania aplikacji.

### 5. Otwórz w przeglądarce
```
http://localhost:8000
```
✅ Wpisz URL firmy → „Oceń firmę" → dostajesz ocenę.

---

## Zatrzymanie
W terminalu z serwerem naciśnij **Ctrl + C**.

## Częste problemy

| Objaw | Przyczyna | Rozwiązanie |
|-------|-----------|-------------|
| `NetworkError` w przeglądarce | serwer nie działa lub otworzyłeś plik bezpośrednio | odpal `uvicorn` i wejdź na `http://localhost:8000` |
| `OPENAI_API_KEY` błąd | brak klucza w `.env` | dodaj klucz do `backend/.env` |
| `Address already in use` | serwer już działa na 8000 | użyj innego portu: `uvicorn app:app --port 8001` |

---

## Najszybciej: `start.bat`
W głównym folderze `Partner-Finder` jest **`start.bat`** — **podwójny klik** odpala serwer
i sam otwiera przeglądarkę. Nie musisz nic wpisywać. (Serwer działa w otwartym oknie —
zamknięcie okna = zatrzymanie serwera.)

---

## Uruchomienie na INNYM komputerze (np. z pracy)

Repo jest na GitHubie, więc na dowolnym laptopie z gitem:

1. **Zainstaluj** Pythona 3.12+ oraz git (jeśli ich nie ma).
2. **Sklonuj repo:**
   ```
   git clone https://github.com/95adampanas-cmd/Partner-Finder.git
   cd Partner-Finder/backend
   ```
3. **Zainstaluj biblioteki:**
   ```
   pip install -r requirements.txt
   ```
4. ⚠️ **NAJWAŻNIEJSZE — utwórz plik `backend/.env` z kluczem.**
   Klucza NIE ma na GitHubie (to sekret, jest w `.gitignore`!). Musisz go dodać ręcznie:
   ```
   OPENAI_API_KEY=sk-...
   ```
   (skopiuj klucz ze swojego konta OpenAI albo z domowego `.env`)
5. **Odpal:** `uvicorn app:app --reload` (albo podwójny klik `start.bat`)
6. **Otwórz:** http://localhost:8000

> 🔑 Pułapka do zapamiętania: `.env` z kluczem **nie jest w gicie** (chroni sekret).
> Na każdym nowym komputerze trzeba go odtworzyć ręcznie — reszta przyjdzie z GitHuba.

---

## Analogia
- **Frontend** = pilot 📱  ·  **Backend** = telewizor 📺
- Sam pilot nic nie zrobi, gdy TV wyłączony. Najpierw włącz serwer, potem działa strona.
