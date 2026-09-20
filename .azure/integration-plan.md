# Integration Plan

## Backend
- Folder: repository root
- Install: `python -m pip install -e ".[dev]"`
- Run: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Build: `docker build -t sdlc-automation .`
- Health: `GET /health`

## Routes
- `GET /health` -> `{ "status": "ok" }`
- `POST /webhook/github` -> signature-checked `pull_request` event; returns `202 accepted`, `202 ignored`, `401`, `422`, or `503`.

## Client seams
- GitHub: `app.github_client.PullRequestClient`; replace `PyGithubClient` only at composition time.
- LLM: `app.graph.workflow.build_workflow(writer_model, auditor_model)`; inject test or Azure OpenAI models.
- Webhook processing: `app.main.process_pull_request(payload, github, workflow)`.

## Remaining integration work
- Configure `GITHUB_TOKEN`, `GITHUB_WEBHOOK_SECRET`, and Azure OpenAI settings in the deployment environment.
- Validate GitHub webhook delivery and repository permissions.
- Run the live workflow against a test pull request and confirm comment formatting.
- Add Azure Container Apps deployment configuration when deployment is requested.

No database or seed data is used or required.

## Integration Results

- Scaffold validation: `7 passed` with `python -m pytest`.
- Compile validation: `python -m compileall -q app` completed successfully.
- Live backend smoke test: Uvicorn started on `127.0.0.1:8000`.
- `GET /health` returned `200` with `{"status":"ok"}`.
- Unsigned `POST /webhook/github` returned `401 Unauthorized`.
- The backend stopped cleanly after probing; no frontend or database integration applies.