from types import SimpleNamespace

from app.graph.agents.ba_agent import ba_agent_node
from app.graph.state import SDLCState


class MalformedModel:
    def invoke(self, messages):
        return SimpleNamespace(content="not JSON")


def test_malformed_ba_response_is_blocked_without_state_content() -> None:
    state: SDLCState = {
        "messages": [], "repo_name": "org/repo", "pr_number": 1,
        "source_code": "x = 1", "git_diff": "+x",
    }

    result = ba_agent_node(MalformedModel())(state)

    assert result["ba_status"] == "blocked"
    assert result["requirements_summary"] == ""