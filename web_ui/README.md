# Bass-ic Finance Web UI

Modern, drag-and-drop web interface for uploading video production scripts.

## Features

- 🎨 **Beautiful Design**: Premium gradients, smooth animations, glassmorphism
- 📁 **Drag & Drop**: Intuitive file upload for scripts and style guides
- ☁️ **Cloud Integration**: Direct upload to Google Cloud Storage
- 📊 **Status Tracking**: View recent productions and their status
- 📱 **Responsive**: Works on desktop, tablet, and mobile

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
export GCP_PROJECT=manhwa-engine
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Run locally
python main.py
```

Access at: http://localhost:8080

## Deploy to Cloud Run

```bash
./deploy.sh
```

The script will:
1. Build container image
2. Deploy to Cloud Run
3. Output the public URL

## Usage

1. **Upload Script**: Drag and drop or click to select your JSON script file
2. **Add Style Guide** (Optional): Upload custom styling instructions
3. **Start Production**: Click the button to upload and trigger video generation

The files will be uploaded to `gs://bass-ic-scripts/` and trigger the Antigravity workflow automatically.

## Security

- Uses service account authentication
- No API keys exposed to frontend
- Cloud Run handles all credentials securely
