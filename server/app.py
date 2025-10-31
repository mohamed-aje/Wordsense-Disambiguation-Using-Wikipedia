from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import re
import os
import json
from pathlib import Path
from datetime import datetime
import uuid

# NLTK setup
import nltk
from nltk.corpus import wordnet as wn
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Wikipedia API
import wikipedia

app = FastAPI(title="WSD Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "message": "WSD backend running"}

@app.get("/api/health")
async def health():
    return {"ok": True}

class LeskRequest(BaseModel):
    sentence: str
    target: str
    pos: Optional[str] = None

class LeskSense(BaseModel):
    synset: Optional[str]
    definition: Optional[str]
    examples: List[str] = []
    lemma_names: List[str] = []
    overlap_count: int = 0
    overlaps: List[str] = []

class LeskResponse(BaseModel):
    target: str
    sentence: str
    best_sense: Optional[LeskSense]
    candidates: List[LeskSense]
    algorithm: str = "lesk_wordnet"

class WikiSense(BaseModel):
    title: str
    summary: str
    url: Optional[str] = None
    overlap_count: int = 0
    overlaps: List[str] = []

class WikiResponse(BaseModel):
    target: str
    sentence: str
    best_sense: Optional[WikiSense]
    candidates: List[WikiSense]
    algorithm: str = "lesk_wikipedia"


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RUNS_DIR = DATA_DIR / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)

try:
    from config import AQUAINT_DIR, DEBUG
except Exception:
    AQUAINT_DIR = BASE_DIR / "data" / "aquaint"
    DEBUG = False


def _ensure_nltk_data() -> None:
    """Ensure required NLTK resources are available at runtime."""
    resources = [
        ("tokenizers/punkt", "punkt"),
        ("corpora/wordnet", "wordnet"),
        ("corpora/omw-1.4", "omw-1.4"),
        ("corpora/stopwords", "stopwords"),
        ("tokenizers/punkt_tab", "punkt_tab"),
    ]
    for res, pkg in resources:
        try:
            nltk.data.find(res)
        except LookupError:
            try:
                nltk.download(pkg, quiet=True)
            except Exception:
                pass


def _normalize_tokens(text: str) -> List[str]:
    """Lowercase, tokenize, remove non-alphabetic tokens and stopwords."""
    try:
        tokens = [t.lower() for t in word_tokenize(text)]
    except LookupError:
        tokens = re.findall(r"[a-z]+", text.lower())
    tokens = [re.sub(r"[^a-z]", "", t) for t in tokens]
    tokens = [t for t in tokens if t]
    try:
        stops = set(stopwords.words("english"))
    except LookupError:
        stops = set()
    return [t for t in tokens if t not in stops]


def compute_lesk_wordnet(sentence: str, target: str, pos: Optional[str] = None) -> Dict[str, Any]:
    """Simplified Lesk using WordNet (definition + examples)."""
    target_l = target.lower()
    ctx_tokens = _normalize_tokens(sentence)
    ctx_tokens = [t for t in ctx_tokens if t != target_l]
    context = set(ctx_tokens)

    pos_map = {"n": wn.NOUN, "v": wn.VERB, "a": wn.ADJ, "r": wn.ADV}
    wn_pos = pos_map.get(pos.lower(), None) if pos else None

    synsets = wn.synsets(target, pos=wn_pos) if wn_pos else wn.synsets(target)
    candidates: List[LeskSense] = []

    for ss in synsets:
        gloss_text = ss.definition() + " " + " ".join(ss.examples())
        gloss_tokens = _normalize_tokens(gloss_text)
        gloss_tokens = [t for t in gloss_tokens if t != target_l]
        overlaps = sorted(context.intersection(set(gloss_tokens)))
        candidates.append(
            LeskSense(
                synset=ss.name(),
                definition=ss.definition(),
                examples=list(ss.examples()),
                lemma_names=list(ss.lemma_names()),
                overlap_count=len(overlaps),
                overlaps=overlaps,
            )
        )

    best = None
    if candidates:
        best = max(candidates, key=lambda c: (c.overlap_count, len(c.examples)))

    return {
        "candidates": [c.model_dump() for c in candidates],
        "best_sense": best.model_dump() if best else None,
    }


@app.on_event("startup")
async def _startup_event():
    _ensure_nltk_data()


@app.post("/api/lesk/wordnet", response_model=LeskResponse)
async def lesk_wordnet(req: LeskRequest):
    if not req.sentence or not req.target:
        raise HTTPException(status_code=400, detail="Both 'sentence' and 'target' are required.")

    result = compute_lesk_wordnet(req.sentence, req.target, req.pos)
    return LeskResponse(
        target=req.target,
        sentence=req.sentence,
        best_sense=result["best_sense"],
        candidates=[LeskSense(**c) for c in result["candidates"]],
    )


def lesk_wikipedia(sentence: str, target: str, max_candidates: int = 15) -> Dict[str, Any]:
    """Lesk using Wikipedia summaries from disambiguation options."""
    target_l = target.lower()
    ctx_tokens = _normalize_tokens(sentence)
    ctx_tokens = [t for t in ctx_tokens if t != target_l]
    context = set(ctx_tokens)

    titles: List[str] = []
    try:
        _ = wikipedia.page(target, auto_suggest=False, redirect=True, preload=False)
        titles = wikipedia.search(target)[:max_candidates]
    except wikipedia.DisambiguationError as e:
        titles = e.options[:max_candidates]
    except wikipedia.PageError:
        titles = wikipedia.search(target)[:max_candidates]
    except Exception:
        titles = wikipedia.search(target)[:max_candidates]

    candidates: List[WikiSense] = []

    for title in titles:
        try:
            summary = wikipedia.summary(title, sentences=3, auto_suggest=False, redirect=True)
        except wikipedia.DisambiguationError:
            try:
                summary = wikipedia.summary(title + " (disambiguation)", sentences=2)
            except Exception:
                continue
        except Exception:
            continue

        gloss_tokens = _normalize_tokens(summary)
        gloss_tokens = [t for t in gloss_tokens if t != target_l]
        overlaps = sorted(context.intersection(set(gloss_tokens)))

        url = None
        if len(candidates) < 5 and len(overlaps) > 0:
            try:
                page = wikipedia.page(title, auto_suggest=False, redirect=True, preload=False)
                url = page.url
            except Exception:
                url = None

        candidates.append(
            WikiSense(
                title=title,
                summary=summary,
                url=url,
                overlap_count=len(overlaps),
                overlaps=overlaps,
            )
        )

    best = None
    if candidates:
        best = max(candidates, key=lambda c: (c.overlap_count, len(c.summary)))

    return {
        "candidates": [c.model_dump() for c in candidates],
        "best_sense": best.model_dump() if best else None,
    }


@app.post("/api/lesk/wiki", response_model=WikiResponse)
async def lesk_wiki(req: LeskRequest):
    if not req.sentence or not req.target:
        raise HTTPException(status_code=400, detail="Both 'sentence' and 'target' are required.")

    result = lesk_wikipedia(req.sentence, req.target)
    return WikiResponse(
        target=req.target,
        sentence=req.sentence,
        best_sense=result["best_sense"],
        candidates=[WikiSense(**c) for c in result["candidates"]],
    )




class AquaintRunRequest(BaseModel):
    target: str
    limit: int = 50
    method: str = "wikipedia"  # or "wordnet"

class AquaintDocResult(BaseModel):
    file: str
    sentence: Optional[str] = None
    best: Optional[Dict[str, Any]] = None
    candidates_count: int = 0

class AquaintRunResponse(BaseModel):
    run_id: str
    target: str
    processed: int
    found_sentences: int
    method: str
    results_file: str


def _iter_aquaint_files(aquaint_dir: Path):
    if not aquaint_dir.exists():
        return
    for root, _dirs, files in os.walk(aquaint_dir):
        for name in sorted(files):
            p = Path(root) / name
            if p.suffix.lower() in {".txt", ".sgm", ".sgml", ".xml", ""}:
                yield p


def _extract_sentences(text: str) -> List[str]:
    try:
        return nltk.sent_tokenize(text)
    except LookupError:
        return re.split(r"(?<=[.!?])\s+", text)


def _read_text_file(path: Path) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def _run_aquaint_batch(target: str, limit: int, method: str) -> Dict[str, Any]:
    processed = 0
    found = 0
    results: List[Dict[str, Any]] = []

    tgt_l = target.lower()
    for fp in _iter_aquaint_files(AQUAINT_DIR):
        if processed >= limit:
            break
        processed += 1
        text = _read_text_file(fp)
        if not text:
            results.append({"file": str(fp), "sentence": None, "best": None, "candidates_count": 0})
            continue

        sent = None
        for s in _extract_sentences(text):
            if tgt_l in s.lower():
                sent = s.strip()
                break

        if not sent:
            results.append({"file": str(fp), "sentence": None, "best": None, "candidates_count": 0})
            continue

        found += 1
        if method == "wordnet":
            out = compute_lesk_wordnet(sent, target)
        else:
            out = lesk_wikipedia(sent, target)

        best = out.get("best_sense")
        cands = out.get("candidates", [])
        results.append({
            "file": str(fp),
            "sentence": sent,
            "best": best,
            "candidates_count": len(cands),
        })

    run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    out_dir = RUNS_DIR / "aquaint"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{run_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "run_id": run_id,
            "target": target,
            "limit": limit,
            "method": method,
            "processed": processed,
            "found_sentences": found,
            "results": results,
        }, f, ensure_ascii=False, indent=2)

    return {
        "run_id": run_id,
        "target": target,
        "processed": processed,
        "found_sentences": found,
        "method": method,
        "results_file": str(out_path),
    }


@app.post("/api/aquaint/run", response_model=AquaintRunResponse)
async def aquaint_run(req: AquaintRunRequest):
    if not req.target:
        raise HTTPException(status_code=400, detail="'target' is required")
    if req.limit <= 0 or req.limit > 1000:
        raise HTTPException(status_code=400, detail="'limit' must be in 1..1000")
    if not AQUAINT_DIR.exists():
        raise HTTPException(status_code=404, detail=f"AQUAINT_DIR not found: {AQUAINT_DIR}")

    out = _run_aquaint_batch(req.target, req.limit, req.method)
    return AquaintRunResponse(**out)


@app.get("/api/aquaint/result")
async def aquaint_result(run_id: str):
    out_dir = RUNS_DIR / "aquaint"
    path = out_dir / f"{run_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="run_id not found")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data




from service.eval_correlation import run_correlation_eval, DATASETS, load_dataset, try_load_embeddings, sweep_convex_combo
from service.wikisim_wrapper import batch_similarity, wikisim_web_health


class CorrelationRequest(BaseModel):
    datasets: List[str] = ["MC", "RG", "WS353"]


@app.post("/api/eval/correlation")
async def eval_correlation(req: CorrelationRequest):
    for ds in req.datasets:
        if ds not in DATASETS:
            raise HTTPException(status_code=400, detail=f"Unknown dataset: {ds}")

    datasets_dir = DATA_DIR / "datasets"
    if not datasets_dir.exists():
        raise HTTPException(status_code=404, detail=f"Datasets dir not found: {datasets_dir}")

    try:
        results = run_correlation_eval(datasets_dir, req.datasets)
        return {"results": results}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eval failed: {e}")


class ConvexComboRequest(BaseModel):
    dataset: str = "WS353"
    base: str = "fasttext" 


@app.post("/api/eval/convex")
async def eval_convex(req: ConvexComboRequest):
    if req.dataset not in DATASETS:
        raise HTTPException(status_code=400, detail=f"Unknown dataset: {req.dataset}")
    datasets_dir = DATA_DIR / "datasets"
    if not datasets_dir.exists():
        raise HTTPException(status_code=404, detail=f"Datasets dir not found: {datasets_dir}")

    rows = load_dataset(datasets_dir, req.dataset)
    try:
        pairs = [(a, b) for a, b, _ in rows]
        wikisim_scores = batch_similarity(pairs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"WikiSim failed: {e}")

    emb = try_load_embeddings().get(req.base)
    if not emb:
        raise HTTPException(status_code=404, detail=f"Embedding '{req.base}' not available. Set env path and restart.")

    try:
        sweep = sweep_convex_combo(rows, wikisim_scores, emb)
        return {"dataset": req.dataset, "base": req.base, "results": sweep}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Convex combo failed: {e}")


class SimilarityRequest(BaseModel):
    pairs: List[List[str]]


@app.post("/api/wikisim/similarity")
async def wikisim_similarity(req: SimilarityRequest):
    if not req.pairs:
        raise HTTPException(status_code=400, detail="'pairs' is required and must be non-empty")
    pairs: List[tuple[str, str]] = []
    for item in req.pairs:
        if not isinstance(item, list) or len(item) < 2:
            continue
        a = (item[0] or "").strip()
        b = (item[1] or "").strip()
        if a and b:
            pairs.append((a, b))
    if not pairs:
        raise HTTPException(status_code=400, detail="No valid word pairs provided")

    scores = batch_similarity(pairs)
    results = [
        {"a": a, "b": b, "score": s if s is not None else None}
        for (a, b), s in zip(pairs, scores)
    ]
    return {"results": results}


@app.get("/api/wikisim/health")
async def wikisim_health():
    """Report status of configured WikiSim web endpoints.

    Useful when using the hosted API; returns `ok` and per-URL statuses.
    """
    return wikisim_web_health()
