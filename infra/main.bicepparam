using './main.bicep'

param location = readEnvironmentVariable('AZURE_LOCATION')
param acrName = readEnvironmentVariable('AZURE_ACR_NAME')
param containerAppsEnvironmentName = readEnvironmentVariable('AZURE_CONTAINER_ENVIRONMENT_NAME', 'container-apps-env')
param containerAppName = readEnvironmentVariable('AZURE_CONTAINER_APP_NAME', 'sdlc-api')
param imageTag = 'latest'
param deployContainerApp = false
param azureOpenAIEndpoint = readEnvironmentVariable('AZURE_OPENAI_ENDPOINT', '')
param azureOpenAIDeployment = readEnvironmentVariable('AZURE_OPENAI_DEPLOYMENT', '')
param azureOpenAIApiVersion = readEnvironmentVariable('AZURE_OPENAI_API_VERSION', '2024-10-21')
param githubToken = readEnvironmentVariable('GITHUB_TOKEN', '')
param githubWebhookSecret = readEnvironmentVariable('GITHUB_WEBHOOK_SECRET', '')
param azureOpenAIApiKey = readEnvironmentVariable('AZURE_OPENAI_API_KEY', '')
