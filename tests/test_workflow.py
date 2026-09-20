from app.graph.models import AuditResult
from app.graph.workflow import build_workflow
from tests.conftest import FakeAuditor, FakeBA, FakeDeveloper, FakeTester, FakeWriter


def initial_state() -> dict:
    return {
        "messages": [], "repo_name": "org/repo", "pr_number": 1,
        "source_code": "def add(a, b): return a + b", "git_diff": "+ add",
        "requirements_summary": "",
        "implementation_plan": "",
        "qa_findings": "",
        "markdown_doc": "", "audit_score": 0, "audit_feedback": "",
        "is_approved": False, "recursion_count": 0,
    }


def test_workflow_retries_until_approval() -> None:
    workflow = build_workflow(
        FakeWriter(),
        FakeAuditor([AuditResult(is_approved=False, score=50, feedback="Add examples"), AuditResult(is_approved=True, score=95, feedback="Good")]),
    )
    result = workflow.invoke(initial_state())
    assert result["is_approved"] is True
    assert result["recursion_count"] == 2


def test_workflow_caps_at_three_attempts() -> None:
    rejected = [AuditResult(is_approved=False, score=20, feedback="Incomplete") for _ in range(3)]
    result = build_workflow(FakeWriter(), FakeAuditor(rejected)).invoke(initial_state())
    assert result["is_approved"] is False
    assert result["recursion_count"] == 3


def test_workflow_runs_ba_developer_and_tester_roles() -> None:
    workflow = build_workflow(
        FakeWriter(),
        FakeAuditor([AuditResult(is_approved=True, score=95, feedback="Good")]),
        ba_model=FakeBA("As a user, I need documentation"),
        developer_model=FakeDeveloper("Plan: write docs and validate"),
        tester_model=FakeTester("QA: all checks pass"),
    )
    result = workflow.invoke(initial_state())
    assert result["requirements_summary"] == "As a user, I need documentation"
    assert result["implementation_plan"] == "Plan: write docs and validate"
    assert result["qa_findings"] == "QA: all checks pass"


def test_routing_skips_completed_agents() -> None:
    ba_model = FakeBA()
    developer_model = FakeDeveloper()
    tester_model = FakeTester()
    writer_model = FakeWriter()
    auditor_model = FakeAuditor([AuditResult(is_approved=True, score=95, feedback="Good")])
    state = initial_state()
    state.update({
        "ba_status": "ok",
        "requirements_summary": "Existing requirements",
        "developer_status": "ok",
        "implementation_plan": "Existing plan",
        "qa_status": "ok",
        "qa_findings": "Existing QA findings",
    })

    result = build_workflow(
        writer_model,
        auditor_model,
        ba_model=ba_model,
        developer_model=developer_model,
        tester_model=tester_model,
    ).invoke(state)

    assert result["is_approved"] is True
    assert ba_model.calls == 0
    assert developer_model.calls == 0
    assert tester_model.calls == 0
    assert writer_model.calls == 1
    assert auditor_model.calls == 1
