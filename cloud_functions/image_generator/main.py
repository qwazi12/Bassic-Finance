"""
Image Generator Cloud Function
Generates scene images using Gemini 3 Pro Image with character references.
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

@functions_framework.http
def generate_image(request):
    """
    Generate a single scene image using Gemini 3 Pro Image.
    
    Expected JSON:
    {
      "scene_data": {
        "character_prompt": "Bass character description",
        "background_prompt": "Background description",
        "pose_id": 0,
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
    print(f"🎨 Generating scene {scene_num} for episode {episode_number}...")
    
    try:
        # Get reference pose from GCS
        ref_bucket = storage_client.bucket('bass-ic-refs')
        pose_id = scene_data.get('pose_id', 0)
        ref_blob = ref_bucket.blob(f"character_sheet/pose_{pose_id:02d}.png")
        
        if not ref_blob.exists():
            return {'error': f'Reference pose {pose_id} not found'}, 404
        
        ref_image_bytes = ref_blob.download_as_bytes()
        
        # Combine prompts
        full_prompt = f"""
Create a scene in SpongeBob SquarePants animation style with these requirements:

BACKGROUND: {scene_data.get('background_prompt', 'Simple background')}

CHARACTER: {scene_data.get('character_prompt', 'Bass character')}

STYLE REQUIREMENTS:
- Use the character design from the reference image
- SpongeBob SquarePants aesthetic: bright colors, thick outlines, simple shapes
- 16:9 aspect ratio
- High detail, professional animation quality
- Match the pose and character style from reference

Generate at 2K resolution.
"""
        
        # Create image part from reference
        image_part = Part.from_data(
            mime_type="image/png",
            data=ref_image_bytes
        )
        
        # Generate image
        response = model.generate_content(
            [full_prompt, image_part],
            generation_config={
                "temperature": 0.4,
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
            return {'error': 'No image generated in response'}, 500
        
        # Upload to GCS
        output_bucket = storage_client.bucket('bass-ic-images')
        output_path = f"episode_{episode_number:03d}/scene_{scene_num:03d}.png"
        output_blob = output_bucket.blob(output_path)
        output_blob.upload_from_string(image_bytes, content_type='image/png')
        
        print(f"✅ Scene {scene_num} complete: gs://bass-ic-images/{output_path}")
        
        return {
            'status': 'success',
            'image_url': f"gs://bass-ic-images/{output_path}",
            'scene_number': scene_num
        }, 200
        
    except Exception as e:
        print(f"❌ Error generating scene {scene_num}: {str(e)}")
        return {'error': str(e), 'scene_number': scene_num}, 500
