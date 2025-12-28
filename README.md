# Bass-ic Finance Automated Video Production System

Complete automated pipeline for generating SpongeBob-style finance career videos using Google Cloud and Gemini 3 AI models.

## 🎯 What This Does

Converts JSON scripts → 8-minute professional videos with:
- **AI-generated visuals** (Gemini 3 Pro Image)
- **Natural narration** (Google Cloud TTS)
- **Automatic assembly** (FFmpeg on Cloud Run)
- **Cost**: ~$10 per video
- **Time**: 11-15 minutes per video

## 🚀 Quick Start

```bash
# 1. Install gcloud CLI
brew install --cask google-cloud-sdk

# 2. Authenticate
gcloud auth login

# 3. Run setup (interactive)
cd bass-ic-finance-automation
./scripts/setup_project.sh
```

## 📁 Project Structure

```
bass-ic-finance-automation/
├── antigravity/workflow.yaml      # Main orchestration workflow
├── cloud_functions/scene_parser/  # Script → Prompts (Gemini 3 Flash)
├── cloud_run/video_assembler/     # FFmpeg video assembly
├── character_generation/          # Generate Bass character poses
└── scripts/                       # Setup & deployment scripts
```

## 🤖 AI Models Used

- **Script Parsing**: `gemini-3-flash-preview`
- **Image Generation**: `gemini-3-pro-image-preview` (2K, thinking mode)
- **Validation**: `gemini-3-flash-preview`

## 📚 Documentation

- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- [API Reference](docs/API_REFERENCE.md)
- [Walkthrough](../brain/ee8562c0-2208-4d05-9f32-c85054ecf65b/walkthrough.md)

## 🔐 Security

All credentials stored in Google Cloud Secret Manager:
- API keys encrypted at rest
- IAM-based access control
- Service account isolation

## 📝 License

MIT
