from __future__ import annotations

from typing import Dict, List, Tuple, Optional
from pathlib import Path
import csv
import os

from .utils import spearmanr
from .wikisim_wrapper import batch_similarity


DATASETS = {
    "MC": "MC.csv",
    "RG": "RG.csv",
    "WS353": "WS353.csv",
}


def load_dataset(data_dir: Path, key: str) -> List[Tuple[str, str, float]]:
    fname = DATASETS.get(key)
    if not fname:
        raise ValueError(f"Unknown dataset: {key}")
    path = data_dir / fname
    rows: List[Tuple[str, str, float]] = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            w1 = r.get("word1") or r.get("w1") or r.get("a")
            w2 = r.get("word2") or r.get("w2") or r.get("b")
            s = r.get("score") or r.get("human_score") or r.get("gold")
            if not (w1 and w2 and s):
                continue
            try:
                rows.append((w1.strip(), w2.strip(), float(s)))
            except Exception:
                continue
    return rows


def try_load_embeddings() -> Dict[str, object]:
    """Conditionally load local embeddings if configured via env.

    Expected environment variables (optional):
    - WORD2VEC_PATH: path to word2vec binary or keyed vectors
    - GLOVE_PATH: path to GloVe in word2vec format
    - FASTTEXT_PATH: path to FastText .vec or binary
    """
    models: Dict[str, object] = {}
    try:
        from gensim.models import KeyedVectors
    except Exception:
        return models

    def load_if(path_env: str, label: str, binary: bool = False):
        p = os.getenv(path_env)
        if p and Path(p).exists():
            try:
                models[label] = KeyedVectors.load_word2vec_format(p, binary=binary)
            except Exception:
                pass

    load_if("WORD2VEC_PATH", "word2vec", binary=True)
    load_if("GLOVE_PATH", "glove", binary=False)
    load_if("FASTTEXT_PATH", "fasttext", binary=False)
    return models


def _pairs(rows: List[Tuple[str, str, float]]) -> List[Tuple[str, str]]:
    return [(a, b) for a, b, _ in rows]


def _human(rows: List[Tuple[str, str, float]]) -> List[float]:
    return [s for _, _, s in rows]


def eval_wikisim(rows: List[Tuple[str, str, float]]) -> Optional[float]:
    sims = batch_similarity(_pairs(rows))
    # filter None
    paired = [(gt, s) for gt, s in zip(_human(rows), sims) if s is not None]
    if not paired:
        return None
    gt, sv = zip(*paired)
    rho, _ = spearmanr(list(gt), list(sv))
    return rho


def eval_embedding(rows: List[Tuple[str, str, float]], kv) -> Optional[float]:
    sim: List[float] = []
    gold: List[float] = []
    for a, b, s in rows:
        if a in kv and b in kv:
            gold.append(s)
            sim.append(float(kv.similarity(a, b)))
    if not sim:
        return None
    rho, _ = spearmanr(gold, sim)
    return rho


def sweep_convex_combo(rows: List[Tuple[str, str, float]], wikisim_scores: List[Optional[float]], kv) -> Dict[str, float]:
    # Align lists and filter None and OOV pairs
    pairs = _pairs(rows)
    human = _human(rows)
    aligned = []
    for (a, b), gt, ws in zip(pairs, human, wikisim_scores):
        if ws is None:
            continue
        if a in kv and b in kv:
            aligned.append((gt, ws, float(kv.similarity(a, b))))

    results: Dict[str, float] = {}
    if not aligned:
        return results

    for k in range(0, 11):
        alpha = k / 10.0
        gold: List[float] = []
        combo: List[float] = []
        for gt, ws, ft in aligned:
            gold.append(gt)
            combo.append(alpha * ws + (1 - alpha) * ft)
        rho, _ = spearmanr(gold, combo)
        results[f"alpha={alpha:.1f}"] = rho
    return results


def run_correlation_eval(data_dir: Path, datasets: List[str]) -> Dict[str, Dict[str, Optional[float]]]:
    """Compute Spearman correlations for the requested datasets.

    Returns a nested dict: dataset -> method -> score or None
    Methods attempted: wikisim, word2vec, glove, fasttext
    """
    results: Dict[str, Dict[str, Optional[float]]] = {}
    embeddings = try_load_embeddings()

    for name in datasets:
        rows = load_dataset(data_dir, name)
        out: Dict[str, Optional[float]] = {}

        # WikiSim
        try:
            sims = batch_similarity(_pairs(rows))
            paired = [(gt, s) for gt, s in zip(_human(rows), sims) if s is not None]
            if paired:
                gt, sv = zip(*paired)
                rho, _ = spearmanr(list(gt), list(sv))
                out["wikisim"] = rho
            else:
                out["wikisim"] = None
        except Exception:
            out["wikisim"] = None

        # Embeddings
        for label, kv in embeddings.items():
            try:
                out[label] = eval_embedding(rows, kv)
            except Exception:
                out[label] = None

        results[name] = out

    return results
