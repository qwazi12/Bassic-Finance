#!/bin/bash

set -e

PROJECT_ID="manhwa-engine"
SERVICE_NAME="bassic-finance-ui"
REGION="us-central1"

echo "🚀 Deploying Bass-ic Finance Web UI..."

gcloud run deploy ${SERVICE_NAME} \
  --source . \
  --project ${PROJECT_ID} \
  --region ${REGION} \
  --platform managed \
  --memory 512Mi \
  --timeout 60s \
  --allow-unauthenticated \
  --service-account bass-ic-automation@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="GCP_PROJECT=${PROJECT_ID}"

echo "✅ Deployment complete!"
echo "🌐 Access your UI at:"
gcloud run services describe ${SERVICE_NAME} --region=${REGION} --format="value(status.url)"
