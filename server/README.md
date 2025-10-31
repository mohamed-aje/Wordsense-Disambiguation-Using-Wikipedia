# WSD Backend

FastAPI backend providing Lesk endpoints using WordNet and Wikipedia.


## WikiSim configuration

This project expects either a WikiSim Python module or a CLI.

- Python module: provide a `wikisim` package exposing `similarity(w1, w2) -> float`.
- CLI: set env `WIKISIM_CMD` to an executable that accepts arguments `w1 w2` and prints a single float score to stdout.



## Run locally

```bash
# WSD Backend

FastAPI backend providing Lesk endpoints using WordNet and Wikipedia, plus evaluation utilities and AQUAINT batch processing.

## Endpoints

- GET `/api/health` — quick health check
- POST `/api/lesk/wordnet` — body: `{ sentence, target, pos? }`
- POST `/api/lesk/wiki` — body: `{ sentence, target }`
- POST `/api/aquaint/run` — body: `{ target, limit=50, method: "wikipedia" | "wordnet" }` → runs batch on AQUAINT first N files, saves a JSON, returns summary and `run_id`.
- GET `/api/aquaint/result?run_id=...` — returns the stored JSON for that run.
- POST `/api/eval/correlation` — body: `{ datasets: ["MC","RG","WS353"] }` → computes Spearman correlation for available methods and returns a table.
- POST `/api/eval/convex` — body: `{ dataset: "WS353", base: "fasttext" }` → alpha sweep combining WikiSim with base embedding if available.
- POST `/api/wikisim/similarity` — body: `{ pairs: [["car","automobile"],["king","queen"]] }` → returns per-pair WikiSim scores if configured.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app:app --reload --port 8000
```

Docs: http://127.0.0.1:8000/docs# 

## Run

```bash
python -m venv .venv
source .venv/bin/activate   # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
