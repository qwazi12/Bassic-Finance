# Deployment Guide

## Quick Deploy Everything

### Step 1: Deploy Cloud Functions (10 min)

```bash
# Scene Parser
cd cloud_functions/scene_parser
./deploy.sh

# Image Generator
cd ../image_generator
./deploy.sh

# Audio Generator
cd ../audio_generator
./deploy.sh
```

### Step 2: Deploy Cloud Run (5 min)

```bash
cd ../../cloud_run/video_assembler
./deploy.sh
```

### Step 3: Get Video Assembler URL

```bash
export VIDEO_ASSEMBLER_URL=$(gcloud run services describe video-assembler \
  --region=us-central1 \
  --project=manhwa-engine \
  --format='value(status.url)')

echo "Video Assembler URL: $VIDEO_ASSEMBLER_URL"
```

### Step 4: Update & Deploy Workflow (5 min)

```bash
# Edit workflows/bass-ic-production.yaml
# Replace VIDEO_ASSEMBLER_URL with actual URL (line 112)
# Replace SLACK_WEBHOOK_URL with yours (line 131) or remove notification step

cd ../../workflows
gcloud workflows deploy bass-ic-production \
  --source=bass-ic-production.yaml \
  --location=us-central1 \
  --project=manhwa-engine \
  --service-account=bass-ic-automation@manhwa-engine.iam.gserviceaccount.com
```

### Step 5: Create Eventarc Trigger (2 min)

```bash
gcloud eventarc triggers create bass-ic-trigger \
  --location=us-central1 \
  --destination-workflow=bass-ic-production \
  --destination-workflow-location=us-central1 \
  --event-filters="type=google.cloud.storage.object.v1.finalized" \
  --event-filters="bucket=bass-ic-scripts" \
  --service-account=bass-ic-automation@manhwa-engine.iam.gserviceaccount.com \
  --project=manhwa-engine
```

### Step 6: Generate Character References (User creates manually)

User uploads 20 character pose images to:
`gs://bass-ic-refs/character_sheet/pose_00.png` through `pose_19.png`

OR run the automated generator:
```bash
cd ../character_generation
pip install -r requirements.txt
python generate_character_sheet.py
```

## Test the System

```bash
# Upload a test script
gsutil cp templates/script_template.json gs://bass-ic-scripts/test.json

# Monitor workflow
gcloud workflows executions list bass-ic-production \
  --location=us-central1 \
  --project=manhwa-engine
```

## Expected Timeline

- Script upload → Workflow trigger: 5s
- Scene parsing: 10s
- Image generation (96 images, 8 parallel): 3-5 min
- Audio generation (96 clips, 12 parallel): 1-2 min
- Video assembly: 3-4 min
- **Total: 8-12 minutes per video**

## Cost Estimate

- Gemini 3 Pro Image: ~$3.80 (96 images @ $0.04/image)
- Cloud TTS: ~$1.00 (96 clips)
- Cloud Functions: ~$0.10
- Cloud Run: ~$0.20
- Workflows: ~$0.01
- **~$5-6 per video**
