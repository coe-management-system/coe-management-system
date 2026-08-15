"""
Fuzzy-matching confidence scoring for entity resolution (M2-07).
Used when an Excel value (e.g. department code "CSE ", "cse", "Comp Sci")
does not exactly match a canonical database value, to surface how confident
the system is in a best-guess match rather than silently accepting or
silently rejecting it.
"""

import difflib


def compute_match_confidence(input_value: str, candidate_value: str) -> float:
    """
    Returns a similarity score between 0.0 and 1.0 comparing input_value
    against candidate_value, case-insensitive, whitespace-trimmed.
    """
    if not input_value or not candidate_value:
        return 0.0

    a = input_value.strip().lower()
    b = candidate_value.strip().lower()

    if a == b:
        return 1.0

    return round(difflib.SequenceMatcher(None, a, b).ratio(), 4)


def find_best_match(input_value: str, candidates: list[dict], value_key: str, threshold: float = 0.6) -> dict:
    """
    candidates: list of dicts, each representing a DB row, containing at least value_key.
    Returns a dict with matched (bool), best_candidate (dict or None),
    confidence (float), and all_scores (list, sorted descending).

    A match is only considered "matched" if confidence >= threshold.
    Below threshold, the caller should NOT silently accept the guess -
    it should be surfaced as a low-confidence / unresolved reference.
    """
    if not candidates:
        return {"matched": False, "best_candidate": None, "confidence": 0.0, "all_scores": []}

    scored = []
    for candidate in candidates:
        score = compute_match_confidence(input_value, candidate.get(value_key, ""))
        scored.append({"candidate": candidate, "confidence": score})

    scored.sort(key=lambda x: x["confidence"], reverse=True)
    best = scored[0]

    return {
        "matched": best["confidence"] >= threshold,
        "best_candidate": best["candidate"] if best["confidence"] >= threshold else None,
        "confidence": best["confidence"],
        "all_scores": scored,
    }
