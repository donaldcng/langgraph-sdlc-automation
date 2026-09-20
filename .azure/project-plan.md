# Project Plan

**Status**: Integrated
**Created**: 2026-09-20
**Mode**: NEW

---

## 1. Project Overview

**Goal**: Build a standalone Python FastAPI service that receives GitHub pull request webhooks, retrieves pull request source and diff context with PyGithub, runs a typed centralized LangGraph documentation and auditing workflow, and publishes the final Markdown documentation back to the pull request. The project is designed so that every module is independently testable.

**App Type**: API only

**API Login**: No

**Mode**: NEW

**Deployment Plan**: No deployment plan found

---

## 2. SDLC Automation API — backend

| Component | Technology |
|-----------|-----------|
| **Language** | Python |
| **Runtime** | CPython |
| **Package Manager** | pip |
| **Test Runner** | pytest |
| **Mocking Library** | unittest.mock |
| **Test Command** | `python -m pytest` |
| **Framework** | FastAPI + LangGraph |
| **Validation** | Pydantic v2 |
| **GitHub Integration** | PyGithub for repository, pull request, source, diff, and comment operations |
| **LLM Integration** | Azure OpenAI client with structured auditor output |
| **Orchestration** | docker-compose |
| **Deployment Target** | Azure Container Apps |

The workflow uses a typed `SDLCState` with message history, repository and pull request identifiers, source and diff context, generated Markdown, audit score and feedback, approval state, and retry count. The graph contains documentation writer and structured auditor nodes; failed audits route back to the writer until approval or a maximum of three attempts. The webhook verifies GitHub signatures before scheduling background processing, and processing failures are logged without exposing credentials or silently publishing incomplete documentation.

---

## 3. Services Required

| Azure Service | Role in App | Environment Variable | Default Value (Local) | Classification |
|---------------|------------|----------------------|-----------------------|----------------|
| Azure Container Apps | Host the FastAPI webhook and LangGraph worker process | `AZURE_CONTAINER_APPS_ENVIRONMENT` | Local Docker container | Essential |
| Azure OpenAI | Generate and audit pull request documentation | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT` | Values supplied through local environment | Essential |
| GitHub | Source of webhook events and pull request data; destination for comments | `GITHUB_TOKEN`, `GITHUB_WEBHOOK_SECRET` | Values supplied through local environment | Essential |

No external datastore is planned. LangGraph state remains scoped to each workflow invocation, and GitHub remains the system of record for pull request context and published documentation.

---

## 4. Prerequisites

### Run

| Tool | Service(s) | Installed | Version |
|------|------------|-----------|---------|
| Python / CPython | SDLC Automation API | ✅ | 3.14.2 |
| pip | SDLC Automation API | ❓ | Not confirmed |
| Docker | SDLC Automation API | ❓ | Not confirmed |
| Azure CLI (`az`) | SDLC Automation API | ✅ | 2.85.0 |
| Azure Developer CLI (`azd`) | SDLC Automation API | ❓ | Not confirmed |

### Debug

| Tool | Service(s) | Installed | Version |
|------|------------|-----------|---------|
| Docker Compose | SDLC Automation API | ❓ | Not confirmed |
| VS Code Python extension | SDLC Automation API | ❓ | Not confirmed |
| VS Code Docker extension | SDLC Automation API | ❓ | Not confirmed |

Double-check all tools marked ❓ before running or deploying the service.

---

## 5. Project Structure

```text
.
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── github_client.py
│   └── graph/
│       ├── __init__.py
│       ├── state.py
│       ├── models.py
│       ├── prompts.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── doc_writer.py
│       │   └── auditor.py
│       └── workflow.py
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_webhook.py
│   ├── test_workflow.py
│   ├── test_github_client.py
│   └── test_auditor.py
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── .env.example
```

The implementation must keep configuration loading, GitHub access, graph state, agent nodes, workflow routing, and HTTP delivery independently testable. Tests must mock GitHub and LLM clients, cover valid and invalid webhook signatures, verify source and diff retrieval, exercise approval and retry routing, enforce the three-attempt cap, and verify final PR comment publishing behavior.

---

## 6. Route Definitions

| # | Method | Path | Description | Request Body | Response Body | Status Codes |
|---|--------|------|-------------|-------------|--------------|-------------|
| 1 | GET | `/health` | Liveness and configuration-safe health check for Container Apps probes | — | `{ "status": "ok" }` | 200 |
| 2 | POST | `/webhook/github` | Validate the GitHub signature, accept supported `pull_request` events, and schedule the LangGraph workflow as a FastAPI background task | GitHub webhook JSON plus `X-Hub-Signature-256` and event headers | `{ "status": "accepted" }` | 202, 400, 401, 422 |

The background workflow extracts the repository name and pull request number, retrieves changed files, diff text, and relevant source through PyGithub, invokes the documentation writer and structured auditor, routes failed audits back to the writer up to three total attempts, and posts the final evaluated Markdown document as a pull request comment. Unsupported webhook event types are acknowledged or ignored according to GitHub delivery semantics without starting a workflow.

---

## 7. Next Steps

1. Run **azure-project-scaffold** to execute this approved plan and create the FastAPI, LangGraph, test, Docker, and Azure Container Apps readiness artifacts.
2. Run **azure-project-integrate** to wire the live GitHub and Azure OpenAI clients behind the mocked interfaces and smoke-test the backend.
3. Run **azure-debug-plan** → **azure-debug-generate** for Docker Compose and VS Code debugging.
4. Run the **azure-deploy** agent when ready; it uses **azure-app-onboard** for architecture, cost estimation, IaC generation, provisioning, and health verification.
