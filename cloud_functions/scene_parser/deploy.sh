#!/bin/bash

set -e

PROJECT_ID="manhwa-engine"
FUNCTION_NAME="parse-script"
REGION="us-central1"

echo "🚀 Deploying Cloud Function: ${FUNCTION_NAME}"

gcloud functions deploy ${FUNCTION_NAME} \
  --gen2 \
  --runtime=python312 \
  --region=${REGION} \
  --source=. \
  --entry-point=parse_script_http \
  --trigger-http \
  --allow-unauthenticated \
  --memory=512MB \
  --timeout=300s \
  --project=${PROJECT_ID} \
  --set-env-vars GCP_PROJECT=${PROJECT_ID},GCP_REGION=${REGION}

echo "✅ Deployment complete!"
