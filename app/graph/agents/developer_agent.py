"""Developer implementation planning node."""

from typing import Any

from langchain_core.messages import HumanMessage

from app.graph.parsing import parse_developer_output, response_content
from app.graph.prompts import DEVELOPER_PROMPT
from app.graph.state import SDLCState


def developer_agent_node(model: Any):
    """Create a concrete implementation plan based on the BA summary and code changes."""

    def plan(state: SDLCState) -> dict[str, Any]:
        prompt = DEVELOPER_PROMPT.format(
            requirements_summary=state.get("requirements_summary", ""),
            source_code=state["source_code"],
            git_diff=state["git_diff"],
        )
        response = model.invoke([HumanMessage(content=prompt)])
        parsed = parse_developer_output(response_content(response))

        return {
            "developer_status": parsed.status,
            "implementation_plan": parsed.implementation_plan,
            "tasks": parsed.tasks,
            "files_to_change": parsed.files_to_change,
            "validation_steps": parsed.validation_steps,
            "dependencies": parsed.dependencies,
            "developer_risks": parsed.risks,
            "messages": [response],
        }

    return plan
