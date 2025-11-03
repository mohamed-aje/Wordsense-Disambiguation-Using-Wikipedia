from typing import List, Tuple, Optional, Dict
import os
import subprocess
import json
import re
print("[DEBUG] WIKISIM_CMD =", os.environ.get("WIKISIM_CMD"))
try:
    import requests 
except Exception:
    requests = None  

try:
    import wikipedia as wp  
except Exception:
    wp = None


class WikiSimNotAvailable(Exception):
    pass


def _wiki_title(term: str) -> Optional[str]:
    """Map a raw word to a likely Wikipedia concept title.
    """
    if wp is None:
        return None
    try:
        try:
            page = wp.page(term, auto_suggest=True, redirect=True, preload=False)
            return page.title.replace(" ", "_")
        except Exception:
            pass
        hits = wp.search(term, results=1)
        if hits:
            return hits[0].replace(" ", "_")
    except Exception:
        return None
    return None


def similarity_word_pair(w1: str, w2: str) -> Optional[float]:
    """Compute similarity via hosted WikiSim web API .
    """
    t1 = _wiki_title(w1) or w1
    t2 = _wiki_title(w2) or w2
    candidates: List[Tuple[str, str]] = [(w1, w2)]
    if (t1, t2) != (w1, w2):
        candidates.append((t1, t2))

    web_urls = os.getenv("WIKISIM_WEB_SIM_URL")
    if not (web_urls and requests is not None):
        return None
    urls = [u.strip() for u in web_urls.split(",") if u.strip()]
    for a, b in candidates:
        for url in urls:
            try:
                resp = requests.post(url, data={"task": "sim", "dir": "1", "c1": a, "c2": b}, timeout=10)
                text = (resp.text or "").strip()
                m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
                if m:
                    return float(m.group(0))
            except Exception:
                continue
    return None


def wikisim_web_health() -> Dict[str, object]:
    """Check reachability of the configured WikiSim web endpoints.
    """
    result: Dict[str, object] = {"ok": False, "endpoints": []}
    web_urls = os.getenv("WIKISIM_WEB_SIM_URL")
    if not web_urls or requests is None:
        result["reason"] = "WIKISIM_WEB_SIM_URL not set or 'requests' missing"
        return result
    urls = [u.strip() for u in web_urls.split(",") if u.strip()]
    any_ok = False
    for url in urls:
        entry: Dict[str, object] = {"url": url, "ok": False}
        try:
            resp = requests.post(url, data={"task": "sim", "dir": "1", "c1": "United_States", "c2": "Canada"}, timeout=8)
            m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", resp.text or "")
            if m:
                entry["ok"] = True
                any_ok = True
            else:
                entry["error"] = "no numeric in response"
        except Exception as e:
            entry["error"] = str(e)
        result["endpoints"].append(entry)
    result["ok"] = any_ok
    return result




def batch_similarity(pairs: List[Tuple[str, str]]) -> List[Optional[float]]:
    """Compute similarity using either WikiSim CLI (preferred) or web API."""
    scores: List[Optional[float]] = []
    wikisim_cmd = os.environ.get("WIKISIM_CMD")

    print("[DEBUG] batch_similarity: using WIKISIM_CMD =", wikisim_cmd)
    if not wikisim_cmd:
        # fallback: web version
        for a, b in pairs:
            scores.append(similarity_word_pair(a, b))
        return scores

    for a, b in pairs:
        try:
            # Run the CLI command
            cmd = f'{wikisim_cmd} "{a}" "{b}"'
            print("[DEBUG] Running:", cmd)
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=10
            )
            output = (result.stdout or "").strip()
            # Try to parse float from CLI output
            m = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", output)
            if m:
                scores.append(float(m.group(0)))
            else:
                scores.append(None)
        except subprocess.TimeoutExpired:
            print(f"[WARN] WikiSim timeout for {a}, {b}")
            scores.append(None)
        except Exception as e:
            print(f"[ERROR] WikiSim failed for {a}, {b}: {e}")
            scores.append(None)
    return scores
