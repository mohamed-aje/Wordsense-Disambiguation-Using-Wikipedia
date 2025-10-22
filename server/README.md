# WSD Backend

FastAPI backend providing Lesk endpoints using WordNet and Wikipedia.

## Endpoints

- POST `/api/lesk/wordnet` — body: `{ sentence, target, pos? }`
- POST `/api/lesk/wiki` — body: `{ sentence, target }`

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app:app --reload --port 8000
```

Docs: http://127.0.0.1:8000/docs# Backend Scaffold

## Run

```bash
python -m venv .venv
source .venv/bin/activate   # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
