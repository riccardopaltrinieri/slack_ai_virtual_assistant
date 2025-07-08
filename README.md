# Slack AI Virtual Assistant

This repository contains a Slack bot that integrates with Google's Gemini API and stores conversations in Firestore.
The bot responds to messages in Slack channels, processes them with Gemini, and maintains conversation context.

## Features

- Slack integration using Bolt framework
- Google Gemini API for natural language processing
- Firestore for conversation storage
- Deployable on Google Cloud Run

## Setup

1. Clone the repository
2. Install dependencies with Poetry:
   ```bash
   poetry install
   ```

3. Copy `.env.example` to `.env` and configure your environment variables:
   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and set the following variables:
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `SLACK_APP_TOKEN`: Your Slack app token
   - `SLACK_SIGNING_SECRET`: Your Slack signing secret
   - `GOOGLE_APPLICATION_CREDENTIALS`: Path to your Google Cloud service account key file (for Firestore)

## Development

To install development dependencies with Poetry:

```bash
poetry install --with dev
```

#### Using pre-commit hooks

This project uses pre-commit to run linting and formatting checks automatically before each commit for better code quality.

Install pre-commit:
```bash
poetry run pip install pre-commit
poetry run pre-commit install
```

The pre-commit hooks will now run automatically on each commit. You can also run them manually:
```bash
poetry run pre-commit run --all-files
```

### Running Tests

```bash
poetry run pytest
```

## Running Locally

To run the bot locally:

```bash
python slack-ai-app/main.py
```

## Deploying to Google Cloud Run

### Manual Deployment

1. Build the Docker image:
   ```bash
   docker build -t gcr.io/[YOUR_PROJECT_ID]/slack-ai-app .
   ```

2. Push the image to Google Container Registry:
   ```bash
   docker push gcr.io/[YOUR_PROJECT_ID]/slack-ai-app
   ```

3. Deploy to Cloud Run:
   ```bash
   gcloud run deploy slack-ai-app \
     --image gcr.io/[YOUR_PROJECT_ID]/slack-ai-app \
     --platform managed \
     --region [REGION] \
     --allow-unauthenticated
   ```

4. Set up environment variables in the Cloud Run service:
   - `GEMINI_API_KEY`
   - `SLACK_BOT_TOKEN`
   - `SLACK_APP_TOKEN`
   - `SLACK_SIGNING_SECRET`
   - `INITIAL_CONTEXT_PATH` (optional, defaults to "static/llm_initial_context.json")

5. Configure your Slack app to use the Cloud Run URL as the event subscription URL.

### Automated Deployment with GitHub Actions

This repository includes a GitHub Actions workflow that automates the deployment process to Google Cloud Run. The workflow:

1. Builds the Docker image
2. Pushes it to Google Container Registry (GCR)
3. Deploys to Cloud Run
4. Passes environment variables from the .env file
5. Retrieves secrets from Google Secret Manager

#### Setup for GitHub Actions Deployment

1. Create the following secrets in Google Secret Manager:
   - `SLACK_SIGNING_SECRET`: Your Slack signing secret
   - `SLACK_CLIENT_SECRET`: Your Slack client secret
   - `GEMINI_API_KEY`: Your Google Gemini API key

2. Set up the Workload Identity Federation for GitHub Actions:
   ```bash
   # Create a Workload Identity Pool
   gcloud iam workload-identity-pools create "github-actions-pool" \
     --project="slack-ai-app-[your-project-id]" \
     --location="global" \
     --display-name="GitHub Actions Pool"

   # Create a Workload Identity Provider
   gcloud iam workload-identity-pools providers create-oidc "github-actions-provider" \
     --project="slack-ai-app-[your-project-id]" \
     --location="global" \
     --workload-identity-pool="github-actions-pool" \
     --display-name="GitHub Actions Provider" \
     --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
     --issuer-uri="https://token.actions.githubusercontent.com"

   # Create a service account for GitHub Actions
   gcloud iam service-accounts create "github-actions-service-account" \
     --project="slack-ai-app-[your-project-id]" \
     --description="Service account for GitHub Actions" \
     --display-name="GitHub Actions Service Account"

   # Grant the service account permissions
   gcloud projects add-iam-policy-binding "slack-ai-app-[your-project-id]" \
     --member="serviceAccount:github-actions-service-account@slack-ai-app-[your-project-id].iam.gserviceaccount.com" \
     --role="roles/run.admin"

   gcloud projects add-iam-policy-binding "slack-ai-app-[your-project-id]" \
     --member="serviceAccount:github-actions-service-account@slack-ai-app-[your-project-id].iam.gserviceaccount.com" \
     --role="roles/storage.admin"

   gcloud projects add-iam-policy-binding "slack-ai-app-[your-project-id]" \
     --member="serviceAccount:github-actions-service-account@slack-ai-app-[your-project-id].iam.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"

   gcloud projects add-iam-policy-binding "slack-ai-app-[your-project-id]" \
     --member="serviceAccount:github-actions-service-account@slack-ai-app-[your-project-id].iam.gserviceaccount.com" \
     --role="roles/iam.serviceAccountUser"

   # Allow the GitHub repository to impersonate the service account
   gcloud iam service-accounts add-iam-policy-binding "github-actions-service-account@slack-ai-app-[your-project-id].iam.gserviceaccount.com" \
     --project="slack-ai-app-[your-project-id]" \
     --role="roles/iam.workloadIdentityUser" \
     --member="principalSet://iam.googleapis.com/projects/slack-ai-app-[your-project-id]/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/[your-google-name]/slack-ai-app"
   ```

3. Add the following secrets to your GitHub repository:
   - `WIF_PROVIDER`: The Workload Identity Provider resource name (e.g., `projects/123456789/locations/global/workloadIdentityPools/github-actions-pool/providers/github-actions-provider`)
   - `WIF_SERVICE_ACCOUNT`: The service account email (e.g., `github-actions-service-account@slack-ai-app-[your-project-id].iam.gserviceaccount.com`)

4. Push to the main branch or manually trigger the workflow to deploy the application.

## Architecture

The application is organized into the following modules:

- `app/api/`: FastAPI routes for handling HTTP requests and Slack events
- `app/config/`: Configuration management and dependency injection
- `app/integrations/`: Integrations with external services (Firestore, Gemini API, MongoDB, Slack)
- `app/interfaces/`: Abstract interfaces for conversation repositories and LLM chat
- `app/models/`: Data models used throughout the application
- `app/static/`: Static files, such as the initial LLM context
- `app/use_cases/`: Business logic and use case implementations (e.g., Slack chat, daily prompt)
- `utils/cron_jobs/`: Cron job configuration files
- `utils/scripts/`: Utility scripts for data fetching and LLM interaction

The main application entry point is in `app/main.py`, which initializes the FastAPI app, configures integrations, and sets up the API routes.
