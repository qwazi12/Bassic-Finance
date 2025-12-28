# Troubleshooting Guide

## Common Issues

### 1. Image Generation Failure (Vertex AI / nano-banana-pro)
**Symptoms:** 
- Workflow fails at `generate-images` step.
- Error logs show `401 Unauthorized` or `500 Internal Server Error`.

**Fix:**
- Check your API key secret: `gcloud secrets versions access latest --secret= -api-key`
- Ensure quota is sufficient for Imagen 3 on your GCP project.
- **Retry:** Re-parsing the script will trigger a fresh run.

### 2. Character Consistency Issues
**Symptoms:**
- "Bass" looks different in some scenes (wrong color, wrong suit).

**Fix:**
- Verify the reference sheet exists: `gsutil ls gs://bass-ic-refs/character_sheet/`
- Regenerate the character sheet:
  ```bash
  cd character_generation
  python generate_character_sheet.py
  ```
- Adjust the `prompt` logic in `cloud_functions/scene_parser/main.py` to be more strict.

### 3. Video Assembler Timeout
**Symptoms:**
- Cloud Run service fails with timeout error (504).
- Logs show "FFmpeg process killed".

**Fix:**
- Increase timeout in `cloud_run/video_assembler/deploy.sh` (e.g., to 900s).
- Increase memory to 8Gi.
- Redeploy: `./scripts/deploy_all.sh`

### 4. Slack Notification Missing
**Symptoms:**
- Video is in Drive, but no Slack message.

**Fix:**
- Check logs: `gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=notification-service"`
- Verify `SLACK_WEBHOOK_URL` secret.

## Support
For critical failures, check the [Cloud Monitoring Dashboard](https://console.cloud.google.com/monitoring).
