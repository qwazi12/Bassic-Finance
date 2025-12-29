#!/bin/bash

set -e

PROJECT_ID="manhwa-engine"
FUNCTION_NAME="generate-image"
REGION="us-central1"

echo "🚀 Deploying Image Generator Cloud Function..."

gcloud functions deploy ${FUNCTION_NAME} \
  --gen2 \
  --runtime=python312 \
  --region=${REGION} \
  --source=. \
  --entry-point=generate_image \
  --trigger-http \
  --allow-unauthenticated \
  --memory=2Gi \
  --timeout=300s \
  --project=${PROJECT_ID} \
  --set-env-vars GCP_PROJECT=${PROJECT_ID}

echo "✅ Image Generator deployed!"
