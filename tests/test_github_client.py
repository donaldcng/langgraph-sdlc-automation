from unittest.mock import Mock

from app.github_client import PyGithubClient


def test_github_client_publishes_comment() -> None:
    github = Mock()
    repo = github.get_repo.return_value
    pull_request = repo.get_pull.return_value
    client = PyGithubClient.__new__(PyGithubClient)
    client._github = github
    client.publish_comment("org/repo", 4, "# Docs")
    pull_request.create_issue_comment.assert_called_once_with("# Docs")
