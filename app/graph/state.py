"""Typed state shared by graph nodes."""

import operator
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage


class SDLCState(TypedDict):
    """State for one PR lifecycle run across BA, developer, QA, writer, and auditor roles."""

    messages: Annotated[Sequence[BaseMessage], operator.add]
    repo_name: str
    pr_number: int
    source_code: str
    git_diff: str

    requirements_summary: str
    ba_status: str
    user_stories: list[str]
    acceptance_criteria: list[str]
    ba_risks: list[str]
    open_questions: list[str]

    implementation_plan: str
    developer_status: str
    tasks: list[str]
    files_to_change: list[str]
    validation_steps: list[str]
    dependencies: list[str]
    developer_risks: list[str]

    qa_findings: str
    qa_status: str
    test_plan: list[str]
    qa_risks: list[str]
    blockers: list[str]
    smoke_checks: list[str]
    qa_verdict: str

    markdown_doc: str
    writer_status: str
    doc_sections: list[str]
    doc_assumptions: list[str]
    missing_context: list[str]

    audit_score: int
    audit_feedback: str
    failing_sections: list[str]
    required_revisions: list[str]
    is_approved: bool
    recursion_count: int
