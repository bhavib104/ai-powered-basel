"""Response generation.

The generation layer only *writes answers*; all authoritative numbers come from
deterministic services.  Retrieved passages are treated as **untrusted data**,
never as instructions.  When no model is available (mock / offline), the answer
is composed deterministically from the evidence so the pipeline always runs.
"""

from __future__ import annotations

import logging

from app.providers.base import LLMProvider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a cautious regulatory risk-analysis assistant.\n"
    "Rules:\n"
    "1. Answer ONLY from the numbered evidence passages provided below. Never invent facts, paragraphs, or citations.\n"
    "2. Cite passages inline like [1], [2] referencing the numbered passages.\n"
    "3. If the evidence is not enough to answer, explicitly say the evidence is insufficient and what would be needed.\n"
    "4. Never give a numeric risk weight or capital value that is not present in the evidence; deterministic tools and stored records are authoritative.\n"
    "5. Be concise and professional."
)


def _evidence_block(evidence: list[dict[str, object]]) -> str:
    lines: list[str] = []
    for i, item in enumerate(evidence, start=1):
        src = item.get("source", "?")
        section = item.get("section")
        page = item.get("page")
        loc = ", ".join(x for x in (f"p.{page}" if page else None, f"§{section}" if section else None) if x)
        lines.append(f"[{i}] {src}{' (' + loc + ')' if loc else ''}:\n{item.get('text', '')}")
    return "\n\n".join(lines)


def synthesize(
    question: str,
    evidence: list[dict[str, object]],
    provider: LLMProvider,
) -> str:
    """Return an answer grounded in ``evidence``, with graceful degradation."""
    if provider.is_mock or any(not e.get("text") for e in evidence):
        return compose_deterministic(question, evidence)

    user_prompt = (
        f"Question: {question}\n\n"
        f"Evidence passages:\n{_evidence_block(evidence)}\n\n"
        "Answer the question using only the passages above."
    )
    try:
        text = provider.complete(SYSTEM_PROMPT, user_prompt)
    except Exception as exc:  # noqa: BLE001 - offline/error fallback
        logger.warning("LLM generation failed (%s); using deterministic answer.", exc)
        text = ""
    if not text.strip():
        return compose_deterministic(question, evidence)
    return text.strip()


def compose_deterministic(
    question: str,
    evidence: list[dict[str, object]],
) -> str:
    """Deterministic, evidence-grounded answer (no model required).

    Deliberately explicit about the evidence used so every claim is verifiable.
    """
    if not evidence:
        return (
            "Insufficient evidence: I could not find any supporting passages in the "
            "indexed regulatory documents to answer this question. More relevant "
            "regulatory material or structured data is needed."
        )
    points = []
    for i, item in enumerate(evidence, start=1):
        src = item.get("source", "?")
        page = item.get("page")
        section = item.get("section")
        loc = ", ".join(x for x in (f"page {page}" if page else None, f"section '{section}'" if section else None) if x)
        suffix = f" ({loc})" if loc else ""
        snippet = str(item.get("text", "")).strip()[:280]
        points.append(f"{i}. {src}{suffix}: {snippet}")
    header = f"Based on {len(evidence)} retrieved passage(s), the following evidence is relevant to the question."
    return header + "\n\n" + "\n\n".join(points) + (
        "\n\nNote: this deterministic answer summarises retrieved evidence; "
        "it does not assert regulatory compliance."
    )