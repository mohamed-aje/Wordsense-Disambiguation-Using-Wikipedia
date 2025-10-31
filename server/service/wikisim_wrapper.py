from typing import List, Tuple, Optional
import os


class WikiSimNotAvailable(Exception):
    pass


def similarity_word_pair(w1: str, w2: str) -> Optional[float]:
    """Compute similarity via WikiSim if available.

    This is a placeholder that expects either a 'wikisim'
    or an environment variable WIKISIM_CMD pointing to an executable that
    accepts 'w1 w2' and prints a float score.
    """
    try:
        import wikisim  

        try:
            return float(wikisim.similarity(w1, w2))
        except Exception:
            pass
    except Exception:
        pass

    cmd = os.getenv("WIKISIM_CMD")
    if cmd:
        import subprocess, shlex

        try:
            args = shlex.split(cmd) + [w1, w2]
            out = subprocess.check_output(args, text=True, timeout=10)
            return float(out.strip().split()[0])
        except Exception:
            return None

    return None


def batch_similarity(pairs: List[Tuple[str, str]]) -> List[Optional[float]]:
    scores: List[Optional[float]] = []
    for a, b in pairs:
        scores.append(similarity_word_pair(a, b))
    return scores
