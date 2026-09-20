import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_webhook_rejects_invalid_signature() -> None:
    get_settings().github_webhook_secret = "secret"
    response = TestClient(app).post(
        "/webhook/github",
        content=b"{}",
        headers={"X-GitHub-Event": "pull_request", "X-Hub-Signature-256": "sha256=bad"},
    )
    assert response.status_code == 401


def test_webhook_ignores_other_events() -> None:
    secret = "secret"
    get_settings().github_webhook_secret = secret
    body = json.dumps({}).encode()
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    response = TestClient(app).post(
        "/webhook/github", content=body, headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": signature}
    )
    assert response.status_code == 202
    assert response.json() == {"status": "ignored"}


def signed_request(body: bytes, *, event: str = "pull_request", delivery_id: str = "delivery-1") -> dict[str, str]:
    secret = "secret"
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return {
        "X-GitHub-Event": event,
        "X-Hub-Signature-256": signature,
        "X-GitHub-Delivery": delivery_id,
    }


def test_webhook_ignores_unsupported_pull_request_action() -> None:
    get_settings().github_webhook_secret = "secret"
    body = json.dumps({"action": "closed", "repository": {}, "number": 1}).encode()
    response = TestClient(app).post("/webhook/github", content=body, headers=signed_request(body))
    assert response.status_code == 202
    assert response.json() == {"status": "ignored"}


def test_webhook_rejects_duplicate_delivery() -> None:
    get_settings().github_webhook_secret = "secret"
    body = json.dumps({"action": "opened", "repository": {}, "number": 1}).encode()
    headers = signed_request(body, delivery_id="duplicate-delivery")
    client = TestClient(app)
    first = client.post("/webhook/github", content=body, headers=headers)
    second = client.post("/webhook/github", content=body, headers=headers)
    assert first.status_code == 503
    assert second.status_code == 202
    assert second.json() == {"status": "duplicate"}


def test_webhook_requires_delivery_id_for_supported_action() -> None:
    get_settings().github_webhook_secret = "secret"
    body = json.dumps({"action": "opened", "repository": {}, "number": 1}).encode()
    headers = signed_request(body)
    headers.pop("X-GitHub-Delivery")
    response = TestClient(app).post("/webhook/github", content=body, headers=headers)
    assert response.status_code == 422
