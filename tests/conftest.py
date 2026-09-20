"""Shared test helpers."""

import json
from types import SimpleNamespace


class FakeWriter:
    def __init__(self, content: str = "# Documentation") -> None:
        self.content = content
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        return SimpleNamespace(content=json.dumps({
            "status": "ok",
            "notes": "Generated documentation",
            "markdown_doc": self.content,
            "sections": ["Summary"],
            "assumptions": [],
            "missing_context": [],
        }))


class FakeAuditor:
    def __init__(self, results) -> None:
        self.results = iter(results)
        self.calls = 0

    def with_structured_output(self, model):
        return self

    def invoke(self, messages):
        self.calls += 1
        return next(self.results)


class FakeBA:
    def __init__(self, content: str = "User story: add docs") -> None:
        self.content = content
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        return SimpleNamespace(content=json.dumps({
            "status": "ok",
            "notes": "Requirements captured",
            "summary": self.content,
            "user_stories": [self.content],
            "acceptance_criteria": [],
            "risks": [],
            "open_questions": [],
        }))


class FakeDeveloper:
    def __init__(self, content: str = "Implementation plan: add docs and tests") -> None:
        self.content = content
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        return SimpleNamespace(content=json.dumps({
            "status": "ok",
            "notes": "Implementation plan captured",
            "implementation_plan": self.content,
            "tasks": [],
            "files_to_change": [],
            "validation_steps": [],
            "dependencies": [],
            "risks": [],
        }))


class FakeTester:
    def __init__(self, content: str = "QA result: tests pass") -> None:
        self.content = content
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        return SimpleNamespace(content=json.dumps({
            "status": "ok",
            "notes": self.content,
            "test_plan": [],
            "risks": [],
            "blockers": [],
            "smoke_checks": [],
            "final_verdict": "pass",
        }))
