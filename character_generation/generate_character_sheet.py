"""
Character Sheet Generator
Creates reference poses for Bass character using the master character profile.
"""

import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import storage
import os
import time
import json

PROJECT_ID = "manhwa-engine"
LOCATION = "us-central1"
BUCKET_NAME = "bass-ic-refs"

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)
model = GenerativeModel("gemini-3-pro-image-preview")
storage_client = storage.Client(project=PROJECT_ID)

# Load master character profile
def load_character_profile():
    """Load the canonical Bass character profile."""
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob('templates/bass_character_profile.json')
        if blob.exists():
            return json.loads(blob.download_as_text())
        else:
            print("⚠️ Master profile not found in GCS, using local file")
            with open('../templates/bass_character_profile.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"❌ Error loading profile: {e}")
        return None

CHARACTER_PROFILE = load_character_profile()

# Build character description from profile
def build_character_description():
    """Build detailed character description from master profile."""
    if not CHARACTER_PROFILE:
        return "Yellow fish character in SpongeBob style"
    
    char = CHARACTER_PROFILE['character']
    colors = char['color_palette']
    anatomy = char['anatomy']['proportions']
    outfit = char['default_outfit']['outfit_items']
    style = CHARACTER_PROFILE['render_style']
    
    return f"""
CHARACTER IDENTITY: {char['name']}
Species: {char['species']}
Age: {char['age_category']}

ANATOMY:
- Form: {anatomy['height_type']}
- Head: {anatomy['head_size_ratio']}
- Torso: {anatomy['torso']}
- Arms: {anatomy['arms']}
- Legs: {anatomy['legs']}
- No neck (head directly on torso)

COLOR PALETTE:
- Body: {colors['body_color']}
- Underbelly: {colors['underbelly_color']}
- Dorsal fin: {colors['fin_color']}
- Arm fins: {colors['arm_color']}
- Eyes: {colors['eye_color']}

OUTFIT (Business Professional):
- Jacket: {outfit['jacket']}
- Shirt: {outfit['shirt']}
- Tie: {outfit['tie']}
- Pants: {outfit['pants']}
- Shoes: {outfit['shoes']}

FACIAL FEATURES:
- Eyes: large oval cartoon eyes
- Mouth: simple thin horizontal line
- No nose, no eyebrows by default

RENDER STYLE:
- Art: {style['art']}
- Lines: {style['lines']}
- Color: {style['color_render']}
- Shading: {style['shading']}
- Aspect: {style['aspect_ratio']}

CRITICAL: This character identity is LOCKED. All poses must maintain exact same character design.
"""

BASE_CHARACTER = build_character_description()

# 20 distinct poses (from pose_library.json)
POSES = [
    {"id": 0, "name": "neutral_standing", "description": "Front view, full body, arms relaxed at sides, calm expression."},
    {"id": 1, "name": "smile_confident", "description": "Front mid-shot, small confident smile, arms loosely at sides."},
    {"id": 2, "name": "big_grin_celebrate", "description": "Front full-body, arms raised in a V shape, big excited smile."},
    {"id": 3, "name": "thinking_fist_to_mouth", "description": "Seated or standing 3/4 view, one fin closed in front of mouth, brows slightly furrowed, deep in thought."},
    {"id": 4, "name": "worried_hand_on_head", "description": "Front mid-shot, one fin on top of head, eyes slightly wide, mouth tense."},
    {"id": 5, "name": "stressed_rub_eyes", "description": "Side 3/4 view, one fin rubbing eyes, slouched slightly forward, tired expression."},
    {"id": 6, "name": "angry_lean_forward", "description": "Front mid-shot, Bass leaning toward camera, brows sharply angled down, mouth open mid-rant, one fin pointing forward."},
    {"id": 7, "name": "shock_mouth_wide", "description": "Close-up, eyes huge, mouth wide open, fins slightly lifted, strong surprise reaction."},
    {"id": 8, "name": "sad_slumped", "description": "Front mid-shot, shoulders slumped, eyes downcast, small frown, fins hanging low."},
    {"id": 9, "name": "desk_typing", "description": "Side 3/4 view, seated at desk, both fins on keyboard, focused neutral expression."},
    {"id": 10, "name": "desk_looking_at_monitors", "description": "OTS from behind Bass, multiple monitors with charts, Bass sitting upright, focused."},
    {"id": 11, "name": "phone_to_ear", "description": "Front mid-shot, one fin holding phone to side of head, listening expression."},
    {"id": 12, "name": "looking_down_at_phone", "description": "3/4 view, Bass seated or standing, both fins holding phone in front of chest, screen glow on face, focused eyes."},
    {"id": 13, "name": "coffee_mug", "description": "Front mid-shot, one fin holding coffee mug near mouth, slightly tired half-smile."},
    {"id": 14, "name": "pointing_at_chart", "description": "Side 3/4 view at whiteboard or screen, one fin extended pointing, mouth mid-explanation."},
    {"id": 15, "name": "walking_side_view", "description": "Profile full-body, one leg forward mid-step, briefcase fin-slung, neutral determined expression."},
    {"id": 16, "name": "bed_alarm_4_30am", "description": "Side view in bed, Bass lying under blanket, head on pillow, sleepy half-open eyes looking at glowing 4:30 AM phone on nightstand."},
    {"id": 17, "name": "headshot_neutral", "description": "Tight head-and-shoulders, straight-on, neutral professional expression."},
    {"id": 18, "name": "thumbs_up", "description": "Front mid-shot, one fin giving a big thumbs-up gesture toward camera, friendly smile."},
    {"id": 19, "name": "arms_open_presentation", "description": "Front full-body behind simple podium or mic, arms stretched wide, confident motivational expression."},
]

def generate_pose(pose_data):
    """Generate a specific character pose using master profile."""
    
    prompt = f"""
{BASE_CHARACTER}

SPECIFIC POSE: {pose_data['description']}

Requirements:
- Character on simple neutral background (light gray or white)
- Character centered in frame
- Full clarity of pose and character design
- Exact adherence to character profile above
- 1024x1024 resolution
- Clean professional reference pose

CRITICAL: Maintain EXACT character identity from profile. Same colors, same proportions, same outfit.
"""
    
    print(f"Generating pose {pose_data['id']}: {pose_data['name']}...")
    
    try:
        response = model.generate_content(
            [prompt],
            generation_config={
                "temperature": 0.3,  # Lower for consistency
                "top_p": 0.9,
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
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"character_sheet/pose_{pose_id:02d}.png")
        
        blob.upload_from_string(image_bytes, content_type='image/png')
        
        # Store metadata
        metadata_blob = bucket.blob(f"metadata/pose_{pose_id:02d}.json")
        metadata = {
            "pose_id": pose_id,
            "name": pose_name,
            "description": POSES[pose_id]['description'],
            "profile_version": "1.0"
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
    print(f"🎭 Poses to generate: {len(POSES)}")
    print(f"\n{BASE_CHARACTER}\n")
    
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
