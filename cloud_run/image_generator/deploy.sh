#!/bin/bash

set -e

PROJECT_ID="manhwa-engine"
SERVICE_NAME="image-generator"
REGION="us-central1"

echo "🚀 Deploying Cloud Run service: ${SERVICE_NAME}"

gcloud run deploy ${SERVICE_NAME} \
  --source . \
  --project ${PROJECT_ID} \
  --region ${REGION} \
  --platform managed \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600s \
  --max-instances 10 \
  --concurrency 4 \
  --allow-unauthenticated \
  --service-account bass-ic-automation@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT=${PROJECT_ID}

echo "✅ Deployment complete!"
