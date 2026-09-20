from app.graph.agents.auditor import auditor_node
from app.graph.models import AuditResult
from app.graph.state import SDLCState
from tests.conftest import FakeAuditor


def test_auditor_maps_structured_result() -> None:
    state: SDLCState = {
        "messages": [], "repo_name": "org/repo", "pr_number": 1,
        "source_code": "x = 1", "git_diff": "+x", "markdown_doc": "# x",
        "audit_score": 0, "audit_feedback": "", "is_approved": False, "recursion_count": 1,
    }
    result = auditor_node(FakeAuditor([AuditResult(is_approved=True, score=90, feedback="Accurate")]))(state)
    assert result["is_approved"] is True
    assert result["audit_score"] == 90
