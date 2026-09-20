"""Structured output contracts for every SDLC agent."""

from pydantic import BaseModel, ConfigDict, Field


class AgentResult(BaseModel):
    """Common fields for all agent outputs."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="ok | needs_clarification | blocked | rejected")
    notes: str = Field(default="", description="Short summary to attach to the workflow state")


class BAOutput(AgentResult):
    """Structured requirements output from the BA agent."""

    summary: str = Field(..., description="Business and technical summary of the work")
    user_stories: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class DeveloperOutput(AgentResult):
    """Structured implementation plan output from the developer agent."""

    implementation_plan: str = Field(..., description="Concrete implementation plan")
    tasks: list[str] = Field(default_factory=list)
    files_to_change: list[str] = Field(default_factory=list)
    validation_steps: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class QAOutput(AgentResult):
    """Structured QA findings output from the tester agent."""

    test_plan: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    smoke_checks: list[str] = Field(default_factory=list)
    final_verdict: str = Field(..., description="pass | fail | needs_manual_review")


class WriterOutput(AgentResult):
    """Structured documentation output from the document writer agent."""

    markdown_doc: str = Field(..., description="Final Markdown documentation")
    sections: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    missing_context: list[str] = Field(default_factory=list)


class AuditResult(BaseModel):
    """Evaluation returned by the structured auditor."""

    is_approved: bool
    score: int = Field(ge=0, le=100)
    feedback: str
    failing_sections: list[str] = Field(default_factory=list)
    required_revisions: list[str] = Field(default_factory=list)
