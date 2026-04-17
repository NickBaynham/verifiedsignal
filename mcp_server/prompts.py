"""MCP prompt templates — grounded workflows for Claude."""

from __future__ import annotations

from mcp_server.runtime import mcp


@mcp.prompt(
    name="summarize_model",
    title="Summarize a knowledge model",
    description="Grounded summary using VerifiedSignal tools/resources only.",
)
def summarize_model(model_id: str, version_id: str | None = None) -> str:
    ver = version_id or "(use latest via get_model_version / resources)"
    return (
        "You are assisting with a VerifiedSignal knowledge model "
        "(canonical, versioned data in PostgreSQL).\n\n"
        f"Model id: {model_id}\n"
        f"Version id (optional): {ver}\n\n"
        "Instructions:\n"
        "1. Use the VerifiedSignal MCP tools (get_model_summary, get_model_assets, "
        "get_model_version) or read resources under verifiedsignal://models/... "
        "to load canonical data.\n"
        "2. Summarize what the model currently contains. Separate: (a) facts grounded "
        "in summary_json and included documents, (b) gaps or empty sections, "
        "(c) anything you cannot verify from the data.\n"
        "3. Do not invent document contents not present in tool/resource output. "
        "If body text is not exposed here, say so explicitly.\n"
    )


@mcp.prompt(
    name="analyze_model_for_risks",
    title="Analyze model for risks",
    description="Identify risks, ambiguities, and weak evidence using canonical model data.",
)
def analyze_model_for_risks(model_id: str, version_id: str | None = None) -> str:
    ver = version_id or "(latest)"
    return (
        "Analyze this VerifiedSignal knowledge model for risks and quality issues.\n\n"
        f"Model id: {model_id}\n"
        f"Version id (optional): {ver}\n\n"
        "Use tools/resources to load summary_json and the included-documents list. "
        "Then:\n"
        "1. List plausible operational / compliance / correctness risks suggested by "
        "the model content (or by conspicuous absences).\n"
        "2. Flag contradictions, undefined interfaces, missing evidence, or overclaims.\n"
        "3. For each item, cite which tool output or resource URI grounded it; "
        "mark uncertainty when inferring.\n"
        "Do not claim to have read full source documents unless the tools actually "
        "returned that text.\n"
    )


@mcp.prompt(
    name="design_tests_from_model",
    title="Design tests from a model",
    description="Generate test ideas grounded in the model (and optional focus).",
)
def design_tests_from_model(
    model_id: str,
    version_id: str | None = None,
    testing_focus: str | None = None,
) -> str:
    focus = testing_focus or "(general)"
    ver = version_id or "(latest)"
    return (
        "Design tests from this VerifiedSignal knowledge model.\n\n"
        f"Model id: {model_id}\n"
        f"Version id (optional): {ver}\n"
        f"Testing focus: {focus}\n\n"
        "Steps:\n"
        "1. Load canonical context via get_model_summary and get_model_assets "
        "(and compare_model_versions if multiple versions matter).\n"
        "2. Propose concrete test cases (happy path, negative, edge, non-functional if "
        "relevant) traceable to specific bullets, claims, or services described in "
        "summary_json or document titles.\n"
        "3. Note gaps where the model does not provide enough detail to design a "
        "precise test; suggest what evidence would be needed.\n"
        "Stay grounded: do not assume APIs, SLAs, or behaviors not reflected in the "
        "retrieved model data.\n"
    )


@mcp.prompt(
    name="explain_model_scope",
    title="Explain model scope",
    description="Clarify what is in/out of the model and what evidence it uses.",
)
def explain_model_scope(model_id: str, version_id: str | None = None) -> str:
    ver = version_id or "(latest)"
    return (
        "Explain the scope of this VerifiedSignal knowledge model.\n\n"
        f"Model id: {model_id}\n"
        f"Version id (optional): {ver}\n\n"
        "Using MCP tools/resources:\n"
        "1. What document set is included (assets)? What model type and build status "
        "apply?\n"
        "2. What does summary_json claim to represent (kind, headline, placeholders)?\n"
        "3. What is explicitly out of scope or deferred to future extraction "
        "(e.g. entities, claims graph)?\n"
        "4. What evidence chain exists today (canonical Postgres version + assets vs "
        "any derived search index)?\n"
        "Be precise and cite tool output fields; avoid speculation beyond them.\n"
    )
