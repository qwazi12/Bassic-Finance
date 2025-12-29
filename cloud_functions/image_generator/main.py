"""
Enhanced Image Generator with Strict Generation Rules
Implements deterministic, rule-based image generation with no AI inference.
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

# Load generation rules and profiles
def load_resources():
    """Load all generation resources from GCS."""
    try:
        bucket = storage_client.bucket('bass-ic-refs')
        
        # Character profile
        profile_blob = bucket.blob('templates/bass_character_profile.json')
        character_profile = json.loads(profile_blob.download_as_text()) if profile_blob.exists() else None
        
        # Generation rules
        rules_blob = bucket.blob('templates/generation_rules.json')
        gen_rules = json.loads(rules_blob.download_as_text()) if rules_blob.exists() else None
        
        # Detailed poses
        poses_blob = bucket.blob('templates/detailed_poses.json')
        detailed_poses = json.loads(poses_blob.download_as_text()) if poses_blob.exists() else None
        
        return character_profile, gen_rules, detailed_poses
    except Exception as e:
        print(f"⚠️ Error loading resources: {e}")
        return None, None, None

CHARACTER_PROFILE, GENERATION_RULES, DETAILED_POSES = load_resources()

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

def build_strict_prompt(shot_data, ref_image_bytes):
    """Build prompt following strict generation rules."""
    
    pose_id = shot_data.get('pose_id', 0)
    camera_preset = shot_data.get('camera_preset_id', 'static_mid')
    
    # Check if this pose has detailed specifications
    detailed_pose = None
    if DETAILED_POSES:
        for pose in DETAILED_POSES.get('detailed_poses', []):
            if pose.get('pose_number') == pose_id:
                detailed_pose = pose
                break
    
    # Build strict rules prompt
    rules_text = """
STRICT GENERATION RULES:
- DETERMINISM: Must follow exact specifications, no creative interpretation
- NO INFERENCE: Only render what is explicitly stated
- IMAGE-LOCKED ATTRIBUTES: Character identity from reference image is ABSOLUTE
  - body_shape, species, base_color_palette, fin_shape, face_geometry, eye_shape
- FORBIDDEN: Never age character, change species, add realism/3D unless requested
"""
    
    # Build character spec
    if CHARACTER_PROFILE:
        char = CHARACTER_PROFILE['character']
        colors = char['color_palette']
        outfit = char['default_outfit']['outfit_items']
        
        character_text = f"""
CHARACTER (IMAGE-LOCKED IDENTITY):
Reference image shows the COMPLETE character identity.
Name: {char['name']}
Colors: {colors['body_color']} body, {colors['fin_color']} fins
Outfit: {outfit['jacket']}, {outfit['shirt']}, {outfit['tie']}
CRITICAL: Use EXACT character from reference image - no modifications.
"""
    else:
        character_text = "Use exact character from reference image."
    
    # Build pose specification
    if detailed_pose:
        pose_text = f"""
POSE SPECIFICATION (EXPLICIT):
Camera: {detailed_pose['camera']['view']}, {detailed_pose['camera']['framing']}
Expression: {detailed_pose['expression']}
Body: {json.dumps(detailed_pose['pose'], indent=2)}
"""
    else:
        pose_text = f"""
POSE: Use exact pose from reference image.
Camera Framing: {CAMERA_FRAMING.get(camera_preset, 'mid-shot')}
"""
    
    # Environment (text-only source)
    environment_text = f"""
ENVIRONMENT (TEXT-SPECIFIED):
{shot_data.get('environment', 'blank underwater gradient')}
Lighting: {shot_data.get('lighting_notes', 'flat cartoon lighting')}
"""
    
    # Style (must be explicit)
    style_text = """
RENDER STYLE (EXPLICIT):
- 2D SpongeBob-style animation
- Clean black outlines
- Flat cel-shaded
- Minimal shading
- 16:9 aspect ratio, 2K resolution
"""
    
    full_prompt = f"""
{rules_text}

{character_text}

{pose_text}

{environment_text}

{style_text}

SCENE CONTEXT:
{shot_data.get('narration', '')}

OUTPUT REQUIREMENTS:
- Character identity from reference image is LOCKED
- Only vary: pose (if specified), environment, camera framing
- No creative interpretation beyond explicit instructions
- Maintain exact character colors, proportions, and design
"""
    
    return full_prompt

@functions_framework.http
def generate_image(request):
    """Generate image with strict rule adherence."""
    
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
        
        # Build strict prompt
        prompt = build_strict_prompt(shot_data, ref_image_bytes)
        
        # Create image part from reference
        image_part = Part.from_data(
            mime_type="image/png",
            data=ref_image_bytes
        )
        
        # Generate image with strict settings
        response = model.generate_content(
            [prompt, image_part],
            generation_config={
                "temperature": 0.2,  # Very low for strict adherence
                "top_p": 0.9,
                "top_k": 20,
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
            'rules_version': '1.0',
            'deterministic': 'true'
        }
        
        output_blob.upload_from_string(image_bytes, content_type='image/png')
        
        print(f"✅ Scene {scene_num} complete (strict rules applied)")
        
        return {
            'status': 'success',
            'image_url': f"gs://bass-ic-images/{output_path}",
            'scene_number': scene_num,
            'camera_preset': camera_preset,
            'pose_id': pose_id,
            'rules_applied': True
        }, 200
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {'error': str(e), 'scene_number': scene_num}, 500
