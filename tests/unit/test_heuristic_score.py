"""Heuristic scoring helpers (deterministic, not ML)."""

from app.services.heuristic_score import compute_heuristic_scores


def test_compute_heuristic_empty_body():
    f, ai, dbg = compute_heuristic_scores(None)
    assert f is None and ai is None
    assert dbg.get("reason") == "no_body"


def test_compute_heuristic_repetitive_text_higher_ai_proxy():
    boring = "word " * 200
    _f1, ai1, _ = compute_heuristic_scores(boring)
    varied = " ".join(f"term{i % 50}" for i in range(200))
    _f2, ai2, _ = compute_heuristic_scores(varied)
    assert ai1 is not None and ai2 is not None
    assert ai1 >= ai2
