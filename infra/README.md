# Azure Container Apps deployment

This folder contains the reviewed infrastructure definition for the FastAPI service.

- `main.bicep`: resource group-scoped deployment
- `main.bicepparam`: non-secret parameter file that reads credentials from process environment variables

No Azure deployment is performed by validation. The deployment is intentionally two-phase because the Container App must not start until its image exists in ACR.

## Verified deployment

The foundation deployment was verified successfully in Azure. The ACR image was built with `az acr build`, the Container App reached a healthy revision, and a GitHub `pull_request.synchronize` event produced a Markdown comment on a test PR.

The final successful path required:

1. Building the image before deploying the Container App revision.
2. Removing the unsupported `temperature` parameter for `gpt-5-mini`.
3. Increasing Azure OpenAI quota above the initial 1K TPM / 1 RPM setting.
4. Providing a valid GitHub token with repository read and issue-comment write permissions.
5. Matching the GitHub webhook secret with the Azure `github-webhook-secret` value.

## Before deployment

1. Choose a globally unique lowercase ACR name, 5-50 alphanumeric characters.
2. Confirm the Azure region, subscription, and resource group.
3. Create an Azure OpenAI chat deployment and record its endpoint and deployment name.
4. Create a GitHub App installation token with Contents read, Pull requests read, and Issues write permissions before phase 2.
5. Generate a webhook secret and configure the same value in GitHub before phase 2.
6. Export these values in the current PowerShell session before phase 2. Do not commit them:

```powershell
$env:AZURE_OPENAI_ENDPOINT = 'https://<resource>.openai.azure.com/'
$env:AZURE_OPENAI_DEPLOYMENT = '<deployment-name>'
$env:AZURE_OPENAI_API_KEY = '<key>'
$env:GITHUB_TOKEN = '<installation-token>'
$env:GITHUB_WEBHOOK_SECRET = '<random-secret>'
```

Export `AZURE_LOCATION` and `AZURE_ACR_NAME` before deployment. Optional environment variables `AZURE_CONTAINER_ENVIRONMENT_NAME` and `AZURE_CONTAINER_APP_NAME` control the generic resource names. Phase 1 does not require the workload secrets; phase 2 must receive all of them.

## Two-phase deployment

From the repository root:

```powershell
az account set --subscription '<subscription-id-or-name>'
az group create --name '<resource-group-name>' --location '<azure-region>'

# Phase 1: create ACR, Log Analytics, Container Apps environment, and managed identity.
az deployment group create `
  --resource-group '<resource-group-name>' `
  --template-file infra/main.bicep `
  --parameters infra/main.bicepparam

# Build and push the image using Azure Container Registry's cloud build.
az acr build `
  --registry <acr-name> `
  --image sdlc-automation:latest `
  .

# Phase 2: create the HTTPS Container App after the image exists.
az deployment group create `
  --resource-group '<resource-group-name>' `
  --template-file infra/main.bicep `
  --parameters infra/main.bicepparam deployContainerApp=true
```

The deployment identity needs permission to create resources and role assignments in the resource group. The template gives the Container App's user-assigned managed identity `AcrPull`; ACR admin credentials are disabled.

## Troubleshooting deployment and runtime failures

### Container image is not found

If Azure reports `MANIFEST_UNKNOWN`, verify the exact repository and tag:

```powershell
az acr repository show-tags `
  --name <acr-name> `
  --repository sdlc-automation `
  --output table
```

Build the image before retrying the Container App deployment:

```powershell
az acr build --registry <acr-name> --image sdlc-automation:<immutable-tag> .
```

### Azure OpenAI errors

- `400 unsupported_value` for `temperature`: use the deployed client configuration without `temperature`.
- `429 rate_limit_exceeded`: inspect the deployment's TPM/RPM quota and wait or increase quota before redelivery. A five-agent run can issue multiple model calls.

### GitHub authentication errors

- `401 Bad credentials` during `get_context`: the `github-token` value in Container Apps is invalid or stale. Verify the token locally, replace the Azure secret, and restart/create a new revision.
- `403 Resource not accessible by personal access token` while creating `/issues/comments`: grant Issues: Read and write to the fine-grained token. Contents and Pull requests read permissions are also required for context retrieval.
- `401 Invalid signature` at `/webhook/github`: the GitHub webhook secret and Azure `github-webhook-secret` do not match.

After changing a Container App secret, restart the active revision or create a new revision so the running process reloads the secret. A GitHub redelivery may reuse the same delivery ID; a new commit on the PR creates a fresh `synchronize` delivery.

### Logs and health checks

```powershell
az containerapp logs show `
  --name '<container-app-name>' `
  --resource-group '<resource-group-name>' `
  --type console `
  --tail 100
```

The expected successful log sequence includes `Starting pull request workflow`, `Retrieved pull request context`, `Workflow completed`, and `Published pull request comment`. `/health` returning `{"status":"ok"}` confirms the container is alive, but does not prove the background workflow completed.

Get the endpoint after phase 2:

```powershell
$hostName = az containerapp show `
  --name '<container-app-name>' `
  --resource-group '<resource-group-name>' `
  --query properties.configuration.ingress.fqdn `
  --output tsv

Invoke-RestMethod "https://$hostName/health"
```

## Resource review

- Region: supplied through `AZURE_LOCATION`; choose the region appropriate for your deployment.
- Container App: external HTTPS ingress, port `8000`, one replica, `0.5` vCPU, `1 GiB` memory.
- ACR: Basic SKU, admin login disabled, managed identity pull.
- Logs: Log Analytics workspace with 30-day retention.
- Secrets: GitHub token, webhook secret, and Azure OpenAI key are secure Bicep parameters and Container App secrets. They are not written to the image.
- Azure OpenAI is consumed as an existing service; this template does not create a model deployment.

## Planning cost estimate

This is a planning estimate, not a billing quote. Confirm current prices for your selected region in the Azure Pricing Calculator before deployment.

| Component | Initial assumption | Planning impact |
|---|---|---|
| Container Apps | Consumption plan, 1 replica, 0.5 vCPU / 1 GiB | Usually low tens of USD/month when continuously running; usage and request volume change this |
| Container Registry | Basic | Low single-digit USD/month range |
| Log Analytics | 30-day retention | Low at low traffic; ingestion and verbose logs can become the variable cost |
| Azure OpenAI | One chat deployment | Token-based; potentially the largest variable cost |
| GitHub | GitHub App | No Azure charge; GitHub plan and API limits still apply |

For a low-volume pilot, use a rough budget envelope of **$20-$75/month before Azure OpenAI token usage**, then set an Azure Cost Management budget and alert. Do not treat that range as guaranteed pricing.

## GitHub webhook after deployment

Configure the repository webhook at:

```text
https://<container-app-fqdn>/webhook/github
```

Use `application/json`, the same webhook secret exported above, and subscribe only to Pull requests. The application processes `opened`, `reopened`, `synchronize`, and `ready_for_review`. Verify the endpoint with GitHub's Recent Deliveries page and then run the local-to-live `/health` check.
