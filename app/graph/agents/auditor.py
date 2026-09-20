"""Structured documentation auditor node."""

from typing import Any

from langchain_core.messages import HumanMessage

from app.graph.models import AuditResult
from app.graph.prompts import AUDITOR_PROMPT
from app.graph.state import SDLCState


def auditor_node(model: Any):
    """Create an auditor node using an injectable structured-output model."""

    structured_model = model.with_structured_output(AuditResult)

    def audit(state: SDLCState) -> dict[str, Any]:
        prompt = AUDITOR_PROMPT.format(
            source_code=state["source_code"],
            git_diff=state["git_diff"],
            markdown_doc=state.get("markdown_doc", ""),
        )
        result: AuditResult = structured_model.invoke([HumanMessage(content=prompt)])
        return {
            "audit_score": result.score,
            "audit_feedback": result.feedback,
            "failing_sections": result.failing_sections,
            "required_revisions": result.required_revisions,
            "is_approved": result.is_approved,
            "messages": [HumanMessage(content=f"Audit: {result.feedback}")],
        }

    return audit
