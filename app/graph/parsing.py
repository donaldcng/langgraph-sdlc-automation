"""Strict parsing helpers for structured agent responses."""

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.graph.models import BAOutput, DeveloperOutput, QAOutput, WriterOutput

OutputModel = TypeVar("OutputModel", bound=BaseModel)


def response_content(response: Any) -> str:
    """Extract text from a chat response without accepting non-text structures."""

    content = response.content if hasattr(response, "content") else response
    return content if isinstance(content, str) else str(content)


def parse_agent_output(
    content: str,
    model_type: type[OutputModel],
    *,
    fallback: dict[str, Any],
) -> OutputModel:
    """Validate an agent response or return a blocked, schema-valid result.

    Free-form text and fenced JSON are intentionally rejected. The fallback keeps
    the graph state typed while making the failure visible to downstream agents.
    """

    try:
        return model_type.model_validate_json(content)
    except (TypeError, ValueError, ValidationError) as error:
        return model_type.model_validate(
            {
                **fallback,
                "status": "blocked",
                "notes": f"Invalid structured response: {error}",
            }
        )


def parse_ba_output(content: str) -> BAOutput:
    return parse_agent_output(
        content,
        BAOutput,
        fallback={
            "summary": "",
            "user_stories": [],
            "acceptance_criteria": [],
            "risks": [],
            "open_questions": [],
        },
    )


def parse_developer_output(content: str) -> DeveloperOutput:
    return parse_agent_output(
        content,
        DeveloperOutput,
        fallback={
            "implementation_plan": "",
            "tasks": [],
            "files_to_change": [],
            "validation_steps": [],
            "dependencies": [],
            "risks": [],
        },
    )


def parse_qa_output(content: str) -> QAOutput:
    return parse_agent_output(
        content,
        QAOutput,
        fallback={
            "test_plan": [],
            "risks": [],
            "blockers": [],
            "smoke_checks": [],
            "final_verdict": "needs_manual_review",
        },
    )


def parse_writer_output(content: str) -> WriterOutput:
    return parse_agent_output(
        content,
        WriterOutput,
        fallback={
            "markdown_doc": "",
            "sections": [],
            "assumptions": [],
            "missing_context": [],
        },
    )
