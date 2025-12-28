#!/bin/bash

set -e

PROJECT_ID="bass-ic-finance-prod"
SERVICE_NAME="video-assembler"
REGION="us-central1"

echo "🚀 Deploying Cloud Run service: ${SERVICE_NAME}"

gcloud run deploy ${SERVICE_NAME} \
  --source . \
  --project ${PROJECT_ID} \
  --region ${REGION} \
  --platform managed \
  --memory 4Gi \
  --cpu 2 \
  --timeout 600s \
  --max-instances 10 \
  --concurrency 1 \
  --allow-unauthenticated \
  --service-account bass-ic-automation@${PROJECT_ID}.iam.gserviceaccount.com

echo "✅ Deployment complete!"
