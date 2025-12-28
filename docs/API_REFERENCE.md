# API Reference

## 1. Scene Parser (Cloud Function)
**Endpoint:** `POST https://[REGION]-[PROJECT].cloudfunctions.net/parse-script`

**Input (JSON):**
```json
{
  "bucket": "bass-ic-scripts",
  "name": "script.json"
}
```

**Output (JSON):**
Returns parsed scene objects with generated prompts.

## 2. Video Assembler (Cloud Run)
**Endpoint:** `POST /assemble`

**Input (JSON):**
```json
{
  "episode_number": 1,
  "episode_title": "String",
  "images_bucket": "bass-ic-images",
  "images_path": "episode_001/",
  "audio_bucket": "bass-ic-audio",
  "audio_path": "episode_001/",
  "output_bucket": "bass-ic-videos",
  "output_filename": "final.mp4",
  "total_scenes": 96,
  "duration_per_scene": 5,
  "fps": 24,
  "resolution": "1920x1080"
}
```

**Output (JSON):**
```json
{
  "status": "success",
  "video_url": "gs://...",
  "video_size_mb": 150.5
}
```

## 3. Notification Service (Cloud Run)
**Endpoint:** `POST /notify`

**Input (JSON):**
```json
{
  "title": "Video Ready",
  "message": "Production complete.",
  "video_url": "https://drive.google.com/...",
  "status": "success"
}
```

**Output (JSON):**
```json
{ "status": "sent" }
```
