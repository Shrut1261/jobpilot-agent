#!/usr/bin/env bash
# Deploy JobPilot to Cloud Run. Run this from Google Cloud Shell
# (https://shell.cloud.google.com) after cloning the repo there.
#
# Usage:
#   export GCP_PROJECT=your-project-id
#   export GEMINI_API_KEY=your-gemini-api-key
#   ./deploy.sh
set -euo pipefail

: "${GCP_PROJECT:?Set GCP_PROJECT to your GCP project id}"
: "${GEMINI_API_KEY:?Set GEMINI_API_KEY to your Gemini API key}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-jobpilot-agent}"

gcloud config set project "$GCP_PROJECT"

echo "== Enabling required APIs =="
gcloud services enable run.googleapis.com \
  cloudbuild.googleapis.com \
  firestore.googleapis.com \
  aiplatform.googleapis.com

echo "== Ensuring Firestore database exists (native mode) =="
gcloud firestore databases create --location="$REGION" --type=firestore-native || true

echo "== Building and deploying to Cloud Run =="
gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_API_KEY=${GEMINI_API_KEY},GOOGLE_GENAI_USE_VERTEXAI=FALSE,GEMINI_MODEL=gemini-3.7-flash"

echo "== Done. Service URL: =="
gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)'
