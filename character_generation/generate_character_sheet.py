"""
Character Sheet Generator
Creates reference poses for Bass character using Gemini 3 Pro Image.
"""

import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import storage
import os
import time

PROJECT_ID = "manhwa-engine"
LOCATION = "us-central1"
BUCKET_NAME = "bass-ic-refs"

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-3-pro-image-preview")

# Base character description
BASE_CHARACTER = """
Bass is a fish-like humanoid character in SpongeBob SquarePants animation style.

PHYSICAL FEATURES:
- Orange/coral colored skin (like a goldfish)
- Large, expressive eyes with thick black outlines
- Simple, rounded body shape
- Wearing a dark business suit with tie
- Fins instead of hands (but can gesture like hands)
- Small tail fin
- SpongeBob-style thick outlines on everything

STYLE REQUIREMENTS:
- Bright, saturated colors
- Simple geometric shapes
- Thick black outlines
- Minimal shading (cel-shaded look)
- Cartoon proportions
- Expressive, exaggerated features
"""

# 20 distinct poses
POSES = [
    {"id": 0, "name": "neutral_standing", "description": "Standing straight, neutral expression, arms at sides"},
    {"id": 1, "name": "pointing_forward", "description": "Pointing forward with one fin, confident expression"},
    {"id": 2, "name": "thinking", "description": "Hand on chin, looking up thoughtfully"},
    {"id": 3, "name": "excited_arms_up", "description": "Both arms raised, excited happy expression"},
    {"id": 4, "name": "sitting_desk", "description": "Sitting at desk, hands folded, professional"},
    {"id": 5, "name": "walking_confident", "description": "Walking stride, confident posture"},
    {"id": 6, "name": "explaining_gesturing", "description": "One hand raised explaining, other hand at side"},
    {"id": 7, "name": "looking_computer", "description": "Looking at computer screen, concentrated"},
    {"id": 8, "name": "phone_call", "description": "Holding phone to ear"},
    {"id": 9, "name": "writing_notes", "description": "Looking down, writing on paper"},
    {"id": 10, "name": "presentation_pointing", "description": "Pointing to side as if presenting chart"},
    {"id": 11, "name": "crossed_arms", "description": "Arms crossed, serious expression"},
    {"id": 12, "name": "handshake_ready", "description": "Extending hand for handshake"},
    {"id": 13, "name": "surprised", "description": "Wide eyes, mouth open in surprise, hands up"},
    {"id": 14, "name": "disappointed", "description": "Slumped shoulders, looking down sadly"},
    {"id": 15, "name": "celebrating", "description": "Arms raised in victory, big smile"},
    {"id": 16, "name": "worried", "description": "Hand on forehead, worried expression"},
    {"id": 17, "name": "reading_document", "description": "Holding and reading document"},
    {"id": 18, "name": "coffee_drinking", "description": "Holding coffee cup, casual stance"},
    {"id": 19, "name": "waving_goodbye", "description": "One arm waving goodbye, friendly smile"},
]

def generate_pose(pose_data):
    """Generate a specific character pose."""
    
    prompt = f"""
{BASE_CHARACTER}

SPECIFIC POSE: {pose_data['description']}

Requirements:
- Single character on transparent or simple solid color background
- Character centered in frame
- Full body visible
- SpongeBob SquarePants animation style
- 1024x1024 resolution
- High quality, clean lines
- Consistent with the base character description
"""
    
    print(f"Generating pose {pose_data['id']}: {pose_data['name']}...")
    
    try:
        response = model.generate_content(
            [prompt],
            generation_config={
                "temperature": 0.4,
                "top_p": 0.95,
                "max_output_tokens": 8192,
            }
        )
        
        # Extract image
        image_bytes = None
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_bytes = part.inline_data.data
                        break
        
        if not image_bytes:
            print(f"❌ No image generated for pose {pose_data['id']}")
            return None
        
        return image_bytes
        
    except Exception as e:
        print(f"❌ Error generating pose {pose_data['id']}: {str(e)}")
        return None

def upload_to_gcs(image_bytes, pose_id, pose_name):
    """Upload generated image to Cloud Storage."""
    
    try:
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"character_sheet/pose_{pose_id:02d}.png")
        
        blob.upload_from_string(image_bytes, content_type='image/png')
        
        # Also store metadata
        metadata_blob = bucket.blob(f"metadata/pose_{pose_id:02d}.json")
        import json
        metadata = {
            "pose_id": pose_id,
            "name": pose_name,
            "description": POSES[pose_id]['description']
        }
        metadata_blob.upload_from_string(
            json.dumps(metadata, indent=2),
            content_type='application/json'
        )
        
        print(f"✅ Uploaded pose {pose_id}: gs://{BUCKET_NAME}/character_sheet/pose_{pose_id:02d}.png")
        return True
        
    except Exception as e:
        print(f"❌ Upload error for pose {pose_id}: {str(e)}")
        return False

def main():
    """Generate all 20 character poses."""
    
    print("🎨 Starting character sheet generation...")
    print(f"📦 Project: {PROJECT_ID}")
    print(f"🗄️ Bucket: {BUCKET_NAME}")
    print(f"🎭 Poses to generate: {len(POSES)}\n")
    
    successful = 0
    failed = 0
    
    for i, pose in enumerate(POSES):
        print(f"\n[{i+1}/{len(POSES)}] Processing: {pose['name']}")
        
        # Generate image
        image_bytes = generate_pose(pose)
        
        if image_bytes:
            # Upload to GCS
            if upload_to_gcs(image_bytes, pose['id'], pose['name']):
                successful += 1
            else:
                failed += 1
        else:
            failed += 1
        
        # Rate limiting - wait 3 seconds between requests
        if i < len(POSES) - 1:
            time.sleep(3)
    
    print(f"\n{'='*50}")
    print(f"✅ Character sheet generation complete!")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Total: {len(POSES)}")
    print(f"{'='*50}\n")
    
    print(f"📁 View results at: https://console.cloud.google.com/storage/browser/{BUCKET_NAME}/character_sheet")

if __name__ == "__main__":
    main()
