"""FastAPI entrypoint for GitHub pull request events."""

import hashlib
import hmac
import logging
from typing import Any

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request, status

from app.config import Settings, get_settings
from app.github_client import PullRequestClient, PyGithubClient
from app.webhook_security import DeliveryReplayGuard

logger = logging.getLogger(__name__)
app = FastAPI(title="SDLC Automation API")
MAX_WEBHOOK_BODY_BYTES = 1_000_000
SUPPORTED_PULL_REQUEST_ACTIONS = {"opened", "reopened", "synchronize", "ready_for_review"}
delivery_replay_guard = DeliveryReplayGuard()


def verify_signature(body: bytes, signature: str | None, secret: str | None) -> bool:
    """Verify GitHub's HMAC SHA-256 signature without exposing the secret."""

    if not signature or not secret or not signature.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def process_pull_request(
    payload: dict[str, Any],
    github: PullRequestClient,
    workflow: Any,
    delivery_id: str,
) -> None:
    """Retrieve context, run the graph, and publish only the final result."""

    repo_name = payload["repository"]["full_name"]
    pr_number = payload["number"]
    logger.info("Starting pull request workflow for %s#%s", repo_name, pr_number)
    try:
        source_code, git_diff = github.get_context(repo_name, pr_number)
        logger.info(
            "Retrieved pull request context for %s#%s (%d source chars, %d diff chars)",
            repo_name,
            pr_number,
            len(source_code),
            len(git_diff),
        )
        initial_state = {
            "messages": [],
            "repo_name": repo_name,
            "pr_number": pr_number,
            "source_code": source_code,
            "git_diff": git_diff,
            "requirements_summary": "",
            "implementation_plan": "",
            "qa_findings": "",
            "markdown_doc": "",
            "audit_score": 0,
            "audit_feedback": "",
            "is_approved": False,
            "recursion_count": 0,
        }
        result = workflow.invoke(initial_state)
        logger.info("Workflow completed for %s#%s", repo_name, pr_number)
        github.publish_comment(repo_name, pr_number, result["markdown_doc"])
        logger.info("Published pull request comment for %s#%s", repo_name, pr_number)
    except Exception:
        delivery_replay_guard.release(delivery_id)
        logger.exception("Pull request workflow failed for %s#%s", repo_name, pr_number)
        raise


def create_workflow(settings: Settings) -> Any:
    """Create the live workflow; kept separate so tests can inject a fake."""

    from langchain_openai import AzureChatOpenAI

    model = AzureChatOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        azure_deployment=settings.azure_openai_deployment,
        api_version=settings.azure_openai_api_version,
    )
    from app.graph.workflow import build_workflow

    return build_workflow(model, model, ba_model=model, developer_model=model, tester_model=model)


@app.get("/health")
def health() -> dict[str, str]:
    """Container Apps liveness endpoint."""

    return {"status": "ok"}


@app.post("/webhook/github", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
) -> dict[str, str]:
    """Validate and schedule supported GitHub pull request events."""

    body = await request.body()
    settings = get_settings()
    if len(body) > MAX_WEBHOOK_BODY_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Payload too large")
    if not verify_signature(body, x_hub_signature_256, settings.github_webhook_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    if x_github_event != "pull_request":
        return {"status": "ignored"}
    payload = await request.json()
    if "repository" not in payload or "number" not in payload:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid payload")
    if payload.get("action") not in SUPPORTED_PULL_REQUEST_ACTIONS:
        return {"status": "ignored"}
    delivery_id = request.headers.get("X-GitHub-Delivery")
    if not delivery_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Missing delivery ID")
    if not delivery_replay_guard.claim(delivery_id):
        return {"status": "duplicate"}
    if not settings.github_token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GitHub is not configured")
    background_tasks.add_task(
        process_pull_request,
        payload,
        PyGithubClient(settings.github_token),
        create_workflow(settings),
        delivery_id,
    )
    return {"status": "accepted"}
