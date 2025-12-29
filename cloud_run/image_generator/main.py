"""
Image Generator Cloud Run Service
Handles heavy ML image generation with Gemini 3 Pro Image.
Uses lazy loading to avoid startup timeouts.
"""

from flask import Flask, request, jsonify
import os
import json

# Global variables for lazy initialization
_vertex_initialized = False
_model = None
_storage_client = None
_character_profile = None
_generation_rules = None

app = Flask(__name__)

PROJECT_ID = os.environ.get("GCP_PROJECT", "manhwa-engine")
LOCATION = "us-central1"

def initialize_services():
    """Lazy initialize Vertex AI and other services on first request."""
    global _vertex_initialized, _model, _storage_client, _character_profile, _generation_rules
    
    if _vertex_initialized:
        return
    
    print("🔄 Initializing Vertex AI and loading resources...")
    
    import vertexai
    from vertexai.generative_models import GenerativeModel
    from google.cloud import storage
    
    # Initialize Vertex AI
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    _model = GenerativeModel("gemini-3-pro-image-preview")
    
    # Initialize storage client
    _storage_client = storage.Client(project=PROJECT_ID)
    
    # Load character profile
    try:
        bucket = _storage_client.bucket('bass-ic-refs')
        blob = bucket.blob('templates/bass_character_profile.json')
        if blob.exists():
            _character_profile = json.loads(blob.download_as_text())
    except Exception as e:
        print(f"⚠️ Could not load character profile: {e}")
        _character_profile = None
    
    # Load generation rules
    try:
        bucket = _storage_client.bucket('bass-ic-refs')
        blob = bucket.blob('templates/generation_rules.json')
        if blob.exists():
            _generation_rules = json.loads(blob.download_as_text())
    except Exception as e:
        print(f"⚠️ Could not load generation rules: {e}")
        _generation_rules = None
    
    _vertex_initialized = True
    print("✅ Initialization complete")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

@app.route('/generate-image', methods=['POST'])
def generate_image():
    """Generate scene image with strict rule adherence."""
    
    # Lazy initialize on first request
    initialize_services()
    
    from vertexai.generative_models import Part
    
    request_json = request.get_json(silent=True)
    
    if not request_json:
        return jsonify({'error': 'No JSON payload'}), 400
    
    shot_data = request_json.get('shot_data', {})
    episode_number = request_json.get('episode_number', 1)
    
    scene_num = shot_data.get('scene_number', 0)
    pose_id = shot_data.get('pose_id', 0)
    camera_preset = shot_data.get('camera_preset_id', 'static_mid')
    
    print(f"🎨 Generating scene {scene_num} (pose: {pose_id}, camera: {camera_preset})...")
    
    try:
        # Get reference pose from GCS
        ref_bucket = _storage_client.bucket('bass-ic-refs')
        ref_blob = ref_bucket.blob(f"character_sheet/pose_{pose_id:02d}.png")
        
        if not ref_blob.exists():
            print(f"⚠️ Reference pose {pose_id} not found, using default")
            ref_blob = ref_bucket.blob("character_sheet/pose_00.png")
        
        ref_image_bytes = ref_blob.download_as_bytes()
        
        # Build prompt with strict rules
        prompt = build_strict_prompt(shot_data, camera_preset)
        
        # Create image part from reference
        image_part = Part.from_data(
            mime_type="image/png",
            data=ref_image_bytes
        )
        
        # Generate image with strict settings
        response = _model.generate_content(
            [prompt, image_part],
            generation_config={
                "temperature": 0.2,
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
            return jsonify({'error': 'No image generated'}), 500
        
        # Upload to GCS
        output_bucket = _storage_client.bucket('bass-ic-images')
        output_path = f"episode_{episode_number:03d}/scene_{scene_num:03d}.png"
        output_blob = output_bucket.blob(output_path)
        
        output_blob.metadata = {
            'pose_id': str(pose_id),
            'camera_preset': camera_preset,
            'environment': shot_data.get('environment', ''),
            'rules_version': '1.0',
            'deterministic': 'true'
        }
        
        output_blob.upload_from_string(image_bytes, content_type='image/png')
        
        print(f"✅ Scene {scene_num} complete")
        
        return jsonify({
            'status': 'success',
            'image_url': f"gs://bass-ic-images/{output_path}",
            'scene_number': scene_num,
            'camera_preset': camera_preset,
            'pose_id': pose_id,
            'rules_applied': True
        }), 200
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e), 'scene_number': scene_num}), 500

def build_strict_prompt(shot_data, camera_preset):
    """Build prompt following strict generation rules."""
    
    # Camera framing instructions
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
    
    framing = CAMERA_FRAMING.get(camera_preset, CAMERA_FRAMING['static_mid'])
    
    # Build character description from profile
    if _character_profile:
        char = _character_profile['character']
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
    
    prompt = f"""
STRICT GENERATION RULES:
- DETERMINISM: Must follow exact specifications, no creative interpretation
- NO INFERENCE: Only render what is explicitly stated
- IMAGE-LOCKED ATTRIBUTES: Character identity from reference image is ABSOLUTE
- FORBIDDEN: Never age character, change species, add realism/3D

{character_text}

POSE: Use exact pose from reference image.
Camera Framing: {framing}

ENVIRONMENT:
{shot_data.get('environment', 'blank underwater gradient')}
Lighting: {shot_data.get('lighting_notes', 'flat cartoon lighting')}

RENDER STYLE (EXPLICIT):
- 2D SpongeBob-style animation
- Clean black outlines
- Flat cel-shaded
- Minimal shading
- 16:9 aspect ratio, 2K resolution

SCENE CONTEXT:
{shot_data.get('narration', '')}

CRITICAL RULES:
1. Character identity from reference is LOCKED
2. No modifications to character appearance
3. Only pose and environment vary
"""
    
    return prompt

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
