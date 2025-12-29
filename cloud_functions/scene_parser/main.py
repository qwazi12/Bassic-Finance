"""
Enhanced Scene Parser with Camera & Pose Intelligence
Parses scripts and intelligently assigns camera presets and character poses.
"""

import functions_framework
import json
import os
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

# Initialize Vertex AI
PROJECT_ID = os.environ.get("GCP_PROJECT", "manhwa-engine")
LOCATION = os.environ.get("GCP_REGION", "us-central1")
vertexai.init(project=PROJECT_ID, location=LOCATION)

model = GenerativeModel("gemini-3-flash-preview")
storage_client = storage.Client(project=PROJECT_ID)

# Load presets
def load_presets():
    """Load camera and pose presets from templates."""
    bucket = storage_client.bucket('bass-ic-scripts')
    
    # Load camera presets
    camera_blob = bucket.blob('templates/camera_presets.json')
    if camera_blob.exists():
        camera_data = json.loads(camera_blob.download_as_text())
        camera_presets = camera_data.get('camera_presets', [])
    else:
        camera_presets = []
    
    # Load pose library  
    pose_blob = bucket.blob('templates/pose_library.json')
    if pose_blob.exists():
        pose_data = json.loads(pose_blob.download_as_text())
        pose_library = pose_data.get('pose_library', [])
    else:
        pose_library = []
    
    return camera_presets, pose_library

CAMERA_PRESETS, POSE_LIBRARY = load_presets()

# Enhanced style guide
CINEMATIC_GUIDE = f"""
You are an expert cinematographer for SpongeBob-style 2D animation.

AVAILABLE CAMERA PRESETS:
{json.dumps(CAMERA_PRESETS, indent=2)}

AVAILABLE CHARACTER POSES (Bass):
{json.dumps(POSE_LIBRARY, indent=2)}

Your job: For each scene description, select the BEST camera_preset_id and pose_id that:
1. Matches the emotional tone
2. Creates visual variety (avoid repeating same preset/pose consecutively)
3. Enhances storytelling (e.g., use punch_in_reaction for surprise moments)
4. Maintains cinematic flow (e.g., use slow_push_in for dramatic moments)

CINEMATOGRAPHY PRINCIPLES:
- Use "static_close" for dialogue/reactions
- Use "slow_push_in" for emphasis or revelation
- Use "punch_in_reaction" for shock/surprise
- Use "static_wide" to establish new locations
- Use "ots_monitor" or "pov_phone" for screen interactions
- Vary shot types for visual rhythm

POSE SELECTION:
- Match emotion (e.g., worried_hand_on_head for stress)
- Match activity (e.g., desk_typing for working scenes)
- Use shocked/surprised poses for dramatic moments
- Use confident poses for success moments
"""

@functions_framework.http
def parse_script_http(request):
    """HTTP endpoint for scene parsing with cinematography."""
    
    request_json = request.get_json(silent=True)
    
    if not request_json:
        return {'error': 'No JSON payload'}, 400
    
    bucket_name = request_json.get('bucket')
    file_name = request_json.get('file')
    
    if not bucket_name or not file_name:
        return {'error': 'Missing bucket or file parameter'}, 400
    
    try:
        # Download script
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        script_content = blob.download_as_text()
        script_data = json.loads(script_content)
        
        print(f"📝 Parsing script: {file_name}")
        
        # Extract metadata
        episode_metadata = {
            'title': script_data.get('title', 'Untitled'),
            'number': script_data.get('episode_number', 1),
            'career_type': script_data.get('career_type', 'unknown')
        }
        
        # Process each shot with AI cinematography
        enhanced_shots = []
        shots = script_data.get('shots', [])
        
        for i, shot in enumerate(shots):
            print(f"🎬 Processing shot {i+1}/{len(shots)}")
            
            # Build prompt for Gemini
            prompt = f"""
{CINEMATIC_GUIDE}

SCENE DESCRIPTION:
{shot.get('narration', '')}

Environment: {shot.get('environment', 'office')}
Existing emotion: {shot.get('emotion', 'NEUTRAL')}

Select the best:
1. camera_preset_id (from available presets)
2. pose_id (from 0-19)
3. lighting_notes (brief description)

Respond in JSON:
{{
  "camera_preset_id": "...",
  "pose_id": 0,
  "lighting_notes": "...",
  "reasoning": "brief explanation"
}}
"""
            
            # Get AI recommendation
            response = model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    temperature=0.7,
                    response_mime_type="application/json"
                )
            )
            
            ai_suggestion = json.loads(response.text)
            
            # Enhance shot with AI suggestions
            enhanced_shot = {
                **shot,
                'camera_preset_id': ai_suggestion.get('camera_preset_id', 'static_mid'),
                'pose_id': ai_suggestion.get('pose_id', 0),
                'lighting_notes': ai_suggestion.get('lighting_notes', shot.get('lighting_notes', '')),
                'ai_reasoning': ai_suggestion.get('reasoning', '')
            }
            
            enhanced_shots.append(enhanced_shot)
        
        print(f"✅ Parsed {len(enhanced_shots)} shots with cinematography")
        
        return {
            'status': 'success',
            'episode_metadata': episode_metadata,
            'shots': enhanced_shots,
            'total_shots': len(enhanced_shots)
        }, 200
        
    except Exception as e:
        print(f"❌ Parse error: {str(e)}")
        return {'error': str(e)}, 500
