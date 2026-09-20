"""BA requirement analysis node."""

from typing import Any

from langchain_core.messages import HumanMessage

from app.graph.models import BAOutput
from app.graph.parsing import parse_ba_output, response_content
from app.graph.prompts import BA_PROMPT
from app.graph.state import SDLCState


def ba_agent_node(model: Any):
    """Capture requirements and technical summary from the PR context."""

    def analyze(state: SDLCState) -> dict[str, Any]:
        prompt = BA_PROMPT.format(
            repo_name=state["repo_name"],
            pr_number=state["pr_number"],
            source_code=state["source_code"],
            git_diff=state["git_diff"],
        )
        response = model.invoke([HumanMessage(content=prompt)])
        parsed = parse_ba_output(response_content(response))

        return {
            "ba_status": parsed.status,
            "requirements_summary": parsed.summary,
            "user_stories": parsed.user_stories,
            "acceptance_criteria": parsed.acceptance_criteria,
            "ba_risks": parsed.risks,
            "open_questions": parsed.open_questions,
            "messages": [response],
        }

    return analyze
