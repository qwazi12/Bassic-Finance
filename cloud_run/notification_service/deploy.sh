#!/bin/bash

set -e

PROJECT_ID="bass-ic-finance-prod"
SERVICE_NAME="notification-service"
REGION="us-central1"

echo "🚀 Deploying Cloud Run service: ${SERVICE_NAME}"

# Try to get Slack webhook from secrets if setup, otherwise passing as empty (handling in code)
# In real setup, we'd source this or map the secret in --update-secrets
# For blueprint, we'll map the secret 'slack-webhook' to env var SLACK_WEBHOOK_URL
# Assuming secret 'slack-webhook' exists as per blueprint logic

gcloud run deploy ${SERVICE_NAME} \
  --source . \
  --project ${PROJECT_ID} \
  --region ${REGION} \
  --platform managed \
  --memory 256Mi \
  --timeout 60s \
  --allow-unauthenticated \
  --service-account bass-ic-automation@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-secrets="SLACK_WEBHOOK_URL=slack-webhook:latest"

echo "✅ Deployment complete!"
