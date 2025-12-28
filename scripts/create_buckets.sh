#!/bin/bash

REGION="us-central1"

# Create all buckets
for bucket in bass-ic-scripts bass-ic-refs bass-ic-images bass-ic-audio bass-ic-videos bass-ic-temp; do
  gsutil mb -c STANDARD -l ${REGION} gs://${bucket} 2>/dev/null || echo "Bucket gs://${bucket} exists"
done

# Create folder structure
gsutil -m mkdir \
  gs://bass-ic-refs/character_sheet/ \
  gs://bass-ic-refs/metadata/ 2>/dev/null || true

echo "✅ All buckets created"
