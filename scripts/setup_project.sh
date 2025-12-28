#!/bin/bash

set -e

echo "🚀 Bass-ic Finance Automation - Complete Setup"
echo "=============================================="
echo ""

# Variables
PROJECT_ID="manhwa-engine"
REGION="us-central1"
SA_NAME="bass-ic-automation"

# Step 1: Set project
echo "📦 Step 1: Setting Google Cloud Project to manhwa-engine..."
gcloud config set project ${PROJECT_ID}
echo "✅ Project configured"
echo ""

# Step 2: Enable APIs
echo "🔌 Step 2: Enabling APIs..."
gcloud services enable \
  aiplatform.googleapis.com \
  speech.googleapis.com \
  storage-api.googleapis.com \
  run.googleapis.com \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  eventarc.googleapis.com \
  secretmanager.googleapis.com \
  drive.googleapis.com \
  gmail.googleapis.com \
  compute.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com
echo "✅ APIs enabled"
echo ""

# Step 3: Create service account
echo "🔐 Step 3: Creating Service Account..."
gcloud iam service-accounts create ${SA_NAME} \
  --display-name="Bass-ic Finance Automation" || echo "Service account exists"

SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Wait for service account to propagate
echo "Waiting for service account to propagate..."
sleep 10

# Grant roles
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/aiplatform.user" \
  --quiet

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.admin" \
  --quiet

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.invoker" \
  --quiet

echo "✅ Service account configured"
echo ""

# Step 4: Create storage buckets
echo "🗄️  Step 4: Creating Storage Buckets..."
bash scripts/create_buckets.sh
echo ""

# Step 5: Setup secrets
echo "🔒 Step 5: Setting up Secrets..."
echo "   Enter your   API key:"
read -s  _KEY
echo -n ${ _KEY} | gcloud secrets create  -api-key --data-file=- || echo "Secret exists"

echo "   Enter your Google Drive folder ID:"
read DRIVE_FOLDER
echo -n ${DRIVE_FOLDER} | gcloud secrets create drive-folder-id --data-file=- || echo "Secret exists"

echo "   Enter notification email:"
read NOTIFY_EMAIL
echo -n ${NOTIFY_EMAIL} | gcloud secrets create notification-email --data-file=- || echo "Secret exists"

# Grant access
for secret in  -api-key drive-folder-id notification-email; do
  gcloud secrets add-iam-policy-binding ${secret} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet
done

echo "✅ Secrets configured"
echo ""

# Step 6: Generate character sheet
echo "🎨 Step 6: Generate Character Reference Sheet"
echo "   This will generate 20 character poses (~10 minutes)"
read -p "   Generate now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
  cd character_generation
  export  _API_KEY=${ _KEY}
  python generate_character_sheet.py
  cd ..
else
  echo "   ⚠️  Skipped. Run manually later: cd character_generation && python generate_character_sheet.py"
fi
echo ""

# Step 7: Deploy services
echo "🚀 Step 7: Deploying Cloud Services..."
bash scripts/deploy_all.sh
echo ""

# Step 8: Deploy Antigravity workflow
echo "⚡ Step 8: Deploying Antigravity Workflow..."
cd antigravity
antigravity deploy workflow.yaml --region=${REGION}
cd ..
echo "✅ Workflow deployed"
echo ""

# Summary
echo "=============================================="
echo "✅ SETUP COMPLETE!"
echo "=============================================="
echo ""
echo "📋 Next Steps:"
echo "   1. Verify character sheet: gsutil ls gs://bass-ic-refs/character_sheet/"
echo "   2. Upload test script: gsutil cp templates/script_template.json gs://bass-ic-scripts/"
echo "   3. Monitor workflow: antigravity logs follow bass-ic-finance-video-production"
echo ""
echo "🎉 Your automated video production system is ready!"
