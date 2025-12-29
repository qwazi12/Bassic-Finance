"""
Audio Generator Cloud Function
Generates narration audio using Google Cloud Text-to-Speech.
"""

import functions_framework
import json
from google.cloud import texttospeech_v1 as texttospeech
from google.cloud import storage
import os

PROJECT_ID = os.environ.get("GCP_PROJECT", "manhwa-engine")
storage_client = storage.Client(project=PROJECT_ID)

@functions_framework.http
def generate_audio(request):
    """
    Generate narration audio using Cloud Text-to-Speech.
    
    Expected JSON:
    {
      "scene_data": {
        "narration": "The narration text",
        "emotion": "NEUTRAL",
        "scene_number": 1
      },
      "episode_number": 1
    }
    """
    
    request_json = request.get_json(silent=True)
    
    if not request_json:
        return {'error': 'No JSON payload'}, 400
    
    scene_data = request_json.get('scene_data', {})
    episode_number = request_json.get('episode_number', 1)
    
    scene_num = scene_data.get('scene_number', 0)
    narration = scene_data.get('narration', '')
    
    if not narration:
        return {'error': 'No narration text provided'}, 400
    
    print(f"🎙️ Generating audio for scene {scene_num}...")
    
    try:
        # Initialize TTS client
        client = texttospeech.TextToSpeechClient()
        
        # Configure synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=narration)
        
        # Select voice (calm, detached male voice)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Neural2-J",  # Calm male voice
            ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )
        
        # Configure audio output
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.95,  # Slightly slower for clarity
            pitch=0.0,  # Neutral pitch
            sample_rate_hertz=48000  # High quality
        )
        
        # Generate audio
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Upload to GCS
        audio_bucket = storage_client.bucket('bass-ic-audio')
        output_path = f"episode_{episode_number:03d}/narration_{scene_num:03d}.mp3"
        audio_blob = audio_bucket.blob(output_path)
        audio_blob.upload_from_string(
            response.audio_content,
            content_type='audio/mpeg'
        )
        
        print(f"✅ Audio {scene_num} complete: gs://bass-ic-audio/{output_path}")
        
        return {
            'status': 'success',
            'audio_url': f"gs://bass-ic-audio/{output_path}",
            'scene_number': scene_num,
            'duration_estimate': len(narration.split()) * 0.5  # Rough estimate: ~0.5s per word
        }, 200
        
    except Exception as e:
        print(f"❌ Error generating audio for scene {scene_num}: {str(e)}")
        return {'error': str(e), 'scene_number': scene_num}, 500
