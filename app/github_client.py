"""Injectable GitHub access boundary and PyGithub implementation."""

from typing import Protocol

from github import Github


class PullRequestClient(Protocol):
    """Operations required by the workflow from a pull request."""

    def get_context(self, repo_name: str, pr_number: int) -> tuple[str, str]: ...

    def publish_comment(self, repo_name: str, pr_number: int, body: str) -> None: ...


class PyGithubClient:
    """Adapter around PyGithub; credentials never enter graph state."""

    def __init__(self, token: str) -> None:
        self._github = Github(token)

    def get_context(self, repo_name: str, pr_number: int) -> tuple[str, str]:
        pull_request = self._github.get_repo(repo_name).get_pull(pr_number)
        files = pull_request.get_files()
        diff = "\n".join(f"### {file.filename}\n{file.patch or ''}" for file in files)
        source = "\n".join(
            f"### {file.filename}\n{pull_request.base.repo.get_contents(file.filename, ref=pull_request.head.ref).decoded_content.decode('utf-8')}"
            for file in files
            if file.status != "removed"
        )
        return source, diff

    def publish_comment(self, repo_name: str, pr_number: int, body: str) -> None:
        self._github.get_repo(repo_name).get_pull(pr_number).create_issue_comment(body)
