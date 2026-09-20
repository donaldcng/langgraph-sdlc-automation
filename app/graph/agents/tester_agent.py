"""QA/tester agent node."""

from typing import Any

from langchain_core.messages import HumanMessage

from app.graph.parsing import parse_qa_output, response_content
from app.graph.prompts import QA_PROMPT
from app.graph.state import SDLCState


def tester_agent_node(model: Any):
    """Review the proposed implementation and note test risks or QA findings."""

    def test(state: SDLCState) -> dict[str, Any]:
        prompt = QA_PROMPT.format(
            implementation_plan=state.get("implementation_plan", ""),
            source_code=state["source_code"],
            git_diff=state["git_diff"],
        )
        response = model.invoke([HumanMessage(content=prompt)])
        parsed = parse_qa_output(response_content(response))

        return {
            "qa_status": parsed.status,
            "qa_findings": parsed.notes,
            "test_plan": parsed.test_plan,
            "qa_risks": parsed.risks,
            "blockers": parsed.blockers,
            "smoke_checks": parsed.smoke_checks,
            "qa_verdict": parsed.final_verdict,
            "messages": [response],
        }

    return test
