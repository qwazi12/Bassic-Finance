#!/bin/bash

set -e

echo "🚀 Deploying all Cloud Run services..."

# Deploy video assembler
cd cloud_run/video_assembler
bash deploy.sh
cd ../..

echo "✅ All services deployed!"
