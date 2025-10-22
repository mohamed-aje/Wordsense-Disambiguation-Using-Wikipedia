from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import re

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


def _ensure_nltk_data() -> None:
    """Ensure required NLTK resources are available at runtime.
    Tries to download quietly if missing.
    """
    resources = [
        ("tokenizers/punkt", "punkt"),
        ("corpora/wordnet", "wordnet"),
        ("corpora/omw-1.4", "omw-1.4"),
        ("corpora/stopwords", "stopwords"),
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
    """Lesk using Wikipedia summaries from disambiguation options.
    - Context excludes the target token to avoid trivial overlaps.
    """
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
