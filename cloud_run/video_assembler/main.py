"""
Cloud Run service for FFmpeg video assembly.
Combines 96 scene images with audio into final 8-minute video.
"""

from flask import Flask, request, jsonify
import subprocess
import os
import tempfile
import time
from google.cloud import storage
from pathlib import Path

app = Flask(__name__)
storage_client = storage.Client()

@app.route('/assemble', methods=['POST'])
def assemble_video():
    """
    Assemble video from images and audio.
    
    Expected JSON payload:
    {
      "episode_number": 1,
      "episode_title": "Your Life as a Hedge Fund Analyst",
      "images_bucket": "bass-ic-images",
      "images_path": "episode_001/",
      "audio_bucket": "bass-ic-audio",
      "audio_path": "episode_001/",
      "output_bucket": "bass-ic-videos",
      "output_filename": "hedge_fund_analyst_ep001.mp4",
      "total_scenes": 96,
      "duration_per_scene": 5,
      "fps": 24,
      "resolution": "1920x1080"
    }
    """
    
    start_time = time.time()
    data = request.json
    
    # Create temporary working directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        print(f"📥 Downloading assets for Episode {data['episode_number']}...")
        
        # Download all scene images
        images_dir = tmpdir / "images"
        images_dir.mkdir()
        
        images_bucket = storage_client.bucket(data['images_bucket'])
        for i in range(data['total_scenes']):
            blob_name = f"{data['images_path']}scene_{i:03d}.png"
            blob = images_bucket.blob(blob_name)
            local_path = images_dir / f"scene_{i:03d}.png"
            blob.download_to_filename(str(local_path))
            print(f"  ✓ Downloaded scene {i+1}/{data['total_scenes']}")
        
        # Download all audio clips
        audio_dir = tmpdir / "audio"
        audio_dir.mkdir()
        
        audio_bucket = storage_client.bucket(data['audio_bucket'])
        for i in range(data['total_scenes']):
            blob_name = f"{data['audio_path']}narration_{i:03d}.mp3"
            blob = audio_bucket.blob(blob_name)
            local_path = audio_dir / f"narration_{i:03d}.mp3"
            blob.download_to_filename(str(local_path))
        
        print(f"✅ All assets downloaded ({data['total_scenes']} images + {data['total_scenes']} audio clips)")
        
        # Create FFmpeg concat file for images
        concat_file = tmpdir / "concat.txt"
        with open(concat_file, 'w') as f:
            for i in range(data['total_scenes']):
                f.write(f"file '{images_dir}/scene_{i:03d}.png'\n")
                f.write(f"duration {data['duration_per_scene']}\n")
            # Repeat last image to avoid FFmpeg bug
            f.write(f"file '{images_dir}/scene_{data['total_scenes']-1:03d}.png'\n")
        
        # Concatenate all audio files
        print("🎵 Merging audio tracks...")
        audio_list = tmpdir / "audio_list.txt"
        with open(audio_list, 'w') as f:
            for i in range(data['total_scenes']):
                f.write(f"file '{audio_dir}/narration_{i:03d}.mp3'\n")
        
        full_audio = tmpdir / "full_audio.mp3"
        audio_concat_cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', str(audio_list),
            '-c', 'copy',
            str(full_audio)
        ]
        subprocess.run(audio_concat_cmd, check=True, capture_output=True)
        print("✅ Audio merged")
        
        # Assemble final video
        print("🎬 Assembling final video...")
        output_video = tmpdir / data['output_filename']
        
        width, height = data['resolution'].split('x')
        
        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-i', str(full_audio),
            '-vf', f'scale={width}:{height},fps={data["fps"]}',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '21',  # High quality
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', '48000',
            '-movflags', '+faststart',  # Web optimization
            '-shortest',
            str(output_video)
        ]
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ FFmpeg error: {result.stderr}")
            return jsonify({'error': 'Video assembly failed', 'details': result.stderr}), 500
        
        print("✅ Video assembled successfully")
        
        # Upload final video to GCS
        print("📤 Uploading to Cloud Storage...")
        output_bucket = storage_client.bucket(data['output_bucket'])
        output_blob = output_bucket.blob(f"final/{data['output_filename']}")
        output_blob.upload_from_filename(str(output_video))
        
        # Get file size
        file_size_mb = output_blob.size / (1024 * 1024)
        
        processing_time = time.time() - start_time
        
        print(f"✅ Upload complete!")
        print(f"   Size: {file_size_mb:.2f} MB")
        print(f"   Time: {processing_time:.1f}s")
        
        return jsonify({
            'status': 'success',
            'video_url': f"gs://{data['output_bucket']}/final/{data['output_filename']}",
            'video_size_mb': round(file_size_mb, 2),
            'processing_time_seconds': round(processing_time, 1)
        })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'video-assembler'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
