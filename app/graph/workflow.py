"""LangGraph workflow construction and routing."""

from typing import Any

from langgraph.graph import END, START, StateGraph

from app.graph.agents.auditor import auditor_node
from app.graph.agents.ba_agent import ba_agent_node
from app.graph.agents.developer_agent import developer_agent_node
from app.graph.agents.doc_writer import doc_writer_node
from app.graph.agents.tester_agent import tester_agent_node
from app.graph.state import SDLCState


def _output_ready(state: SDLCState, stage: str) -> bool:
    """Return whether a stage has a usable, validated result already."""

    fields = {
        "ba_agent": ("ba_status", "requirements_summary"),
        "developer_agent": ("developer_status", "implementation_plan"),
        "tester_agent": ("qa_status", "qa_findings"),
        "writer": ("writer_status", "markdown_doc"),
    }
    status_field, output_field = fields[stage]
    return state.get(status_field) == "ok" and bool(state.get(output_field))


def _next_stage(state: SDLCState, stages: list[str], start_index: int) -> str:
    """Choose the next configured stage whose output is not ready."""

    for stage in stages[start_index:]:
        if stage == "auditor" or not _output_ready(state, stage):
            return stage
    return END


def _route_after_audit(state: SDLCState) -> str:
    if state["is_approved"] or state["recursion_count"] >= 3:
        return END
    return "writer"


def build_workflow(
    writer_model: Any,
    auditor_model: Any,
    *,
    ba_model: Any | None = None,
    developer_model: Any | None = None,
    tester_model: Any | None = None,
):
    """Build a compiled workflow spanning BA, developer, QA, writer, and auditor roles."""

    graph = StateGraph(SDLCState)
    configured_stages: list[str] = []

    if ba_model is not None:
        graph.add_node("ba_agent", ba_agent_node(ba_model))
        configured_stages.append("ba_agent")
    if developer_model is not None:
        graph.add_node("developer_agent", developer_agent_node(developer_model))
        configured_stages.append("developer_agent")
    if tester_model is not None:
        graph.add_node("tester_agent", tester_agent_node(tester_model))
        configured_stages.append("tester_agent")

    graph.add_node("writer", doc_writer_node(writer_model))
    configured_stages.append("writer")

    graph.add_node("auditor", auditor_node(auditor_model))
    configured_stages.append("auditor")

    graph.add_conditional_edges(
        START,
        lambda state: _next_stage(state, configured_stages, 0),
    )
    for index, stage in enumerate(configured_stages[:-1]):
        graph.add_conditional_edges(
            stage,
            lambda state, next_index=index + 1: _next_stage(
                state, configured_stages, next_index
            ),
        )
    graph.add_conditional_edges("auditor", _route_after_audit)
    return graph.compile()
