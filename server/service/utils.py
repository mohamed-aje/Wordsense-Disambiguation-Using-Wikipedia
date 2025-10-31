from typing import List, Tuple


def _rank(values: List[float]) -> List[float]:
    indexed = sorted([(v, i) for i, v in enumerate(values)])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][0] == indexed[i][0]:
            j += 1
        avg_rank = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k][1]] = avg_rank
        i = j + 1
    return ranks


def spearmanr(x: List[float], y: List[float]) -> Tuple[float, float]:
    """Return Spearman rank correlation rho and p-value (p-value as 0.0 placeholder).

    Implemented without SciPy to avoid extra dependencies.
    """
    if len(x) != len(y) or len(x) == 0:
        return float("nan"), 0.0
    rx = _rank(x)
    ry = _rank(y)
    n = float(len(x))
    mean_rx = sum(rx) / n
    mean_ry = sum(ry) / n
    num = sum((a - mean_rx) * (b - mean_ry) for a, b in zip(rx, ry))
    den_x = sum((a - mean_rx) ** 2 for a in rx) ** 0.5
    den_y = sum((b - mean_ry) ** 2 for b in ry) ** 0.5
    if den_x == 0 or den_y == 0:
        return float("nan"), 0.0
    rho = num / (den_x * den_y)
    return rho, 0.0
