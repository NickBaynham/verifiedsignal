"""Prompt template content tests."""

from __future__ import annotations

from mcp_server.prompts import analyze_model_for_risks, design_tests_from_model, summarize_model


def test_summarize_model_prompt_mentions_tools():
    text = summarize_model("model-uuid-1", None)
    assert "model-uuid-1" in text
    assert "get_model_summary" in text


def test_design_tests_prompt_includes_focus():
    text = design_tests_from_model("m1", None, "refunds")
    assert "m1" in text
    assert "refunds" in text


def test_risks_prompt_discourages_hallucination():
    text = analyze_model_for_risks("m2", "v3")
    assert "m2" in text
    assert "v3" in text
    assert "Do not claim to have read full source documents" in text
