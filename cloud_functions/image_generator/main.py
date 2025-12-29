"""
Enhanced Image Generator with Master Character Profile
Ensures all generated images use the canonical Bass character design.
"""

import functions_framework
import json
import vertexai
from vertexai.generative_models import GenerativeModel, Part
from google.cloud import storage
import os

PROJECT_ID = os.environ.get("GCP_PROJECT", "manhwa-engine")
LOCATION = "us-central1"
vertexai.init(project=PROJECT_ID, location=LOCATION)

model = GenerativeModel("gemini-3-pro-image-preview")
storage_client = storage.Client(project=PROJECT_ID)

# Load master character profile
def load_character_profile():
    """Load the canonical Bass character profile from GCS."""
    try:
        bucket = storage_client.bucket('bass-ic-refs')
        blob = bucket.blob('templates/bass_character_profile.json')
        if blob.exists():
            return json.loads(blob.download_as_text())
    except:
        pass
    return None

CHARACTER_PROFILE = load_character_profile()

# Build character description
def get_character_description():
    """Get detailed character description from master profile."""
    if not CHARACTER_PROFILE:
        return "Yellow fish character named Bass in SpongeBob style with navy suit"
    
    char = CHARACTER_PROFILE['character']
    colors = char['color_palette']
    outfit = char['default_outfit']['outfit_items']
    
    return f"""
CHARACTER: {char['name']} - {char['species']}
BODY: {colors['body_color']} with {colors['underbelly_color']} underbelly
FINS: {colors['fin_color']} dorsal fin, {colors['arm_color']} arm fins
EYES: {colors['eye_color']}
OUTFIT: {outfit['jacket']}, {outfit['shirt']}, {outfit['tie']}
PROPORTIONS: Short cartoon humanoid (4 heads tall), large rounded head, no neck
FACIAL: Large oval eyes, simple thin mouth line, no nose or eyebrows
STYLE: 2D SpongeBob-style cartoon, clean black outlines, flat cel-shaded
"""

BASS_CHARACTER = get_character_description()

# Camera preset framing instructions
CAMERA_FRAMING = {
    "static_mid": "waist-up mid-shot, character centered, eye-level",
    "static_close": "close-up on face and shoulders",
    "static_wide": "full-body shot, show environment context",
    "slow_push_in": "mid-shot framed for zoom-in animation",
    "slow_pull_out": "slightly tighter frame for zoom-out animation",
    "punch_in_reaction": "close framing for dramatic zoom to face",
    "pan_left_to_right": "wider horizontal frame for left-to-right pan",
    "pan_right_to_left": "wider horizontal frame for right-to-left pan",
    "tilt_up": "frame from lower body to face for upward pan",
    "tilt_down": "frame from face to hands/desk for downward pan",
    "ots_monitor": "over-the-shoulder view from behind, show computer screens",
    "pov_phone": "first-person view looking down at phone screen"
}

@functions_framework.http
def generate_image(request):
    """Generate scene image with master character profile and camera framing."""
    
    request_json = request.get_json(silent=True)
    
    if not request_json:
        return {'error': 'No JSON payload'}, 400
    
    shot_data = request_json.get('shot_data', {})
    episode_number = request_json.get('episode_number', 1)
    
    scene_num = shot_data.get('scene_number', 0)
    pose_id = shot_data.get('pose_id', 0)
    camera_preset = shot_data.get('camera_preset_id', 'static_mid')
    
    print(f"🎨 Generating scene {scene_num} (pose: {pose_id}, camera: {camera_preset})...")
    
    try:
        # Get reference pose from GCS
        ref_bucket = storage_client.bucket('bass-ic-refs')
        ref_blob = ref_bucket.blob(f"character_sheet/pose_{pose_id:02d}.png")
        
        if not ref_blob.exists():
            print(f"⚠️ Reference pose {pose_id} not found, using default")
            ref_blob = ref_bucket.blob("character_sheet/pose_00.png")
        
        ref_image_bytes = ref_blob.download_as_bytes()
        
        # Get camera framing instruction
        framing = CAMERA_FRAMING.get(camera_preset, CAMERA_FRAMING['static_mid'])
        
        # Build comprehensive prompt with master profile
        prompt = f"""
Create a scene in SpongeBob SquarePants animation style.

{BASS_CHARACTER}

CHARACTER POSE:
Use the exact character from the reference image in the exact pose shown.
CRITICAL: Maintain character identity - same colors, proportions, outfit, and style.

CAMERA FRAMING:
{framing}

ENVIRONMENT:
{shot_data.get('environment', 'office interior')}

LIGHTING:
{shot_data.get('lighting_notes', 'natural bright lighting')}

SCENE CONTEXT:
{shot_data.get('narration', '')}

STYLE REQUIREMENTS:
- SpongeBob SquarePants aesthetic: bright saturated colors, thick black outlines, simple shapes
- Match character design EXACTLY from reference and master profile
- 16:9 aspect ratio, 2K resolution
- Flat cel-shaded animation aesthetic
- Minimal shading, clean professional quality
- Frame according to "{camera_preset}" preset

CRITICAL RULES:
1. Character identity is LOCKED - exact colors and design from reference
2. No modifications to character appearance
3. Only pose and environment vary
"""
        
        # Create image part from reference
        image_part = Part.from_data(
            mime_type="image/png",
            data=ref_image_bytes
        )
        
        # Generate image
        response = model.generate_content(
            [prompt, image_part],
            generation_config={
                "temperature": 0.3,  # Lower for character consistency
                "top_p": 0.95,
                "max_output_tokens": 8192,
            }
        )
        
        # Extract generated image
        image_bytes = None
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_bytes = part.inline_data.data
                        break
        
        if not image_bytes:
            return {'error': 'No image generated'}, 500
        
        # Upload to GCS
        output_bucket = storage_client.bucket('bass-ic-images')
        output_path = f"episode_{episode_number:03d}/scene_{scene_num:03d}.png"
        output_blob = output_bucket.blob(output_path)
        
        # Store metadata
        output_blob.metadata = {
            'pose_id': str(pose_id),
            'camera_preset': camera_preset,
            'environment': shot_data.get('environment', ''),
            'profile_version': '1.0'
        }
        
        output_blob.upload_from_string(image_bytes, content_type='image/png')
        
        print(f"✅ Scene {scene_num} complete (camera: {camera_preset})")
        
        return {
            'status': 'success',
            'image_url': f"gs://bass-ic-images/{output_path}",
            'scene_number': scene_num,
            'camera_preset': camera_preset,
            'pose_id': pose_id
        }, 200
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {'error': str(e), 'scene_number': scene_num}, 500
