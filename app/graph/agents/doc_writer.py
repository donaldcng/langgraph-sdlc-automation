"""Documentation writer node."""

from typing import Any

from langchain_core.messages import HumanMessage

from app.graph.parsing import parse_writer_output, response_content
from app.graph.prompts import WRITER_PROMPT
from app.graph.state import SDLCState


def doc_writer_node(model: Any):
    """Create a graph node using an injectable chat model."""

    def write(state: SDLCState) -> dict[str, Any]:
        prompt = WRITER_PROMPT.format(
            repo_name=state["repo_name"],
            pr_number=state["pr_number"],
            source_code=state["source_code"],
            git_diff=state["git_diff"],
            requirements_summary=state.get("requirements_summary", ""),
            implementation_plan=state.get("implementation_plan", ""),
            qa_findings=state.get("qa_findings", ""),
            audit_feedback=state.get("audit_feedback", ""),
        )
        response = model.invoke([HumanMessage(content=prompt)])
        parsed = parse_writer_output(response_content(response))

        return {
            "writer_status": parsed.status,
            "markdown_doc": parsed.markdown_doc,
            "doc_sections": parsed.sections,
            "doc_assumptions": parsed.assumptions,
            "missing_context": parsed.missing_context,
            "messages": [response],
            "recursion_count": state.get("recursion_count", 0) + 1,
        }

    return write
