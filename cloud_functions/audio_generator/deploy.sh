#!/bin/bash

set -e

PROJECT_ID="manhwa-engine"
FUNCTION_NAME="generate-audio"
REGION="us-central1"

echo "🚀 Deploying Audio Generator Cloud Function..."

gcloud functions deploy ${FUNCTION_NAME} \
  --gen2 \
  --runtime=python312 \
  --region=${REGION} \
  --source=. \
  --entry-point=generate_audio \
  --trigger-http \
  --allow-unauthenticated \
  --memory=512MB \
  --timeout=60s \
  --project=${PROJECT_ID} \
  --set-env-vars GCP_PROJECT=${PROJECT_ID}

echo "✅ Audio Generator deployed!"
