"""
Generate 20 reference poses for Bass (the finance fish character).
Ensures visual consistency across all episodes.
"""

import os
import json
import requests
from google.cloud import storage

# Character base description
BASE_CHARACTER = """
SpongeBob SquarePants animation style. Main character named Bass is a friendly fish-like humanoid with:
- Circular yellow-orange head (#F4C466)
- Large expressive dot eyes (black pupils with white shine)
- Simple curved line mouth (expression varies by pose)
- Small oval body wearing navy blue business suit (#1C3A57)
- White dress shirt with red tie
- Simplified mitten-style hands (3 fingers each)
- Short legs with black dress shoes
- Soft painterly shading with cel-shading highlights
- Clean black outlines (3px width)
- Bikini Bottom organic curved aesthetic
Full body visible, centered in frame.
Solid light blue background (#E8F4F8) for easy extraction.
1:1 aspect ratio, 1024x1024 resolution.
"""

# 20 pose definitions
POSES = [
    {
        "id": 0,
        "name": "neutral_standing",
        "description": "Front view, arms at sides, calm dot eyes, slight smile, professional posture"
    },
    {
        "id": 1,
        "name": "happy_smiling",
        "description": "Front view, wide dot eyes with shine, curved smile, relaxed shoulders"
    },
    {
        "id": 2,
        "name": "excited",
        "description": "Front view, extra-wide dot eyes, big curved smile, arms slightly raised, energetic"
    },
    {
        "id": 3,
        "name": "worried_anxious",
        "description": "Front view, downturned mouth, slightly narrowed eyes, tense posture, hand near face"
    },
    {
        "id": 4,
        "name": "stressed_tired",
        "description": "Front view, half-closed tired eyes, frown, slouched posture, hand rubbing forehead"
    },
    {
        "id": 5,
        "name": "angry_frustrated",
        "description": "Front view, furrowed brow lines, downturned frown, clenched fists at sides, tense"
    },
    {
        "id": 6,
        "name": "shocked_surprised",
        "description": "Front view, extremely wide eyes, open circular mouth, hands raised in surprise"
    },
    {
        "id": 7,
        "name": "sleeping",
        "description": "Side view, eyes closed with peaceful expression, lying down position, relaxed"
    },
    {
        "id": 8,
        "name": "sitting_desk",
        "description": "Front view, sitting position, hands resting on desk surface, focused expression"
    },
    {
        "id": 9,
        "name": "looking_screen",
        "description": "Three-quarter view, focused on computer screen (not visible), concentrated expression"
    },
    {
        "id": 10,
        "name": "holding_phone",
        "description": "Front view, simplified phone shape held to ear, listening expression"
    },
    {
        "id": 11,
        "name": "drinking_coffee",
        "description": "Front view, holding coffee mug in both hands, slight smile, relaxed"
    },
    {
        "id": 12,
        "name": "reading_document",
        "description": "Front view, holding paper document in hands, reading with focused eyes downward"
    },
    {
        "id": 13,
        "name": "walking",
        "description": "Side view, mid-step walking pose, arms swinging naturally, forward motion"
    },
    {
        "id": 14,
        "name": "pointing",
        "description": "Front view, right arm extended forward, index finger pointing, assertive expression"
    },
    {
        "id": 15,
        "name": "celebrating",
        "description": "Front view, both arms raised above head, big smile, triumphant pose"
    },
    {
        "id": 16,
        "name": "thinking",
        "description": "Front view, hand on chin, looking upward, contemplative expression"
    },
    {
        "id": 17,
        "name": "sad_disappointed",
        "description": "Front view, downturned curved mouth, droopy eyes, shoulders slumped, dejected"
    },
    {
        "id": 18,
        "name": "professional_headshot",
        "description": "Front view, upper body only, perfect business attire, confident slight smile, promotional pose"
    },
    {
        "id": 19,
        "name": "silhouette",
        "description": "Front view full body silhouette outline only, solid black fill, no internal details, clear shape"
    }
]

def generate_character_pose(pose_data, api_key):
    """Generate a single character pose using nano-banana-pro."""
    
    full_prompt = f"{BASE_CHARACTER}\n\nPose: {pose_data['description']}"
    
    response = requests.post(
        "https://api. .ai/v1/image/generate",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "nano-banana-pro",
            "prompt": full_prompt,
            "aspect_ratio": "1:1",
            "num_images": 1,
            "quality": "high"
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        return result['images'][0]['url']
    else:
        raise Exception(f"Image generation failed: {response.text}")

def upload_to_gcs(local_path, bucket_name, blob_name):
    """Upload file to Google Cloud Storage."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    print(f"✓ Uploaded {blob_name} to gs://{bucket_name}")

def main():
    # Get API key from environment
    api_key = os.environ.get(' _API_KEY')
    if not api_key:
        raise ValueError(" _API_KEY environment variable not set")
    
    # Create output directory
    os.makedirs('character_output', exist_ok=True)
    
    print("🎨 Generating Bass character reference sheet (20 poses)...")
    print(f"Model: nano-banana-pro")
    print(f"Style: SpongeBob SquarePants animation")
    print()
    
    generated_poses = []
    
    for pose in POSES:
        print(f"[{pose['id']:02d}/19] Generating {pose['name']}...")
        
        try:
            image_url = generate_character_pose(pose, api_key)
            
            # Download image
            img_response = requests.get(image_url)
            local_filename = f"character_output/pose_{pose['id']:02d}_{pose['name']}.png"
            
            with open(local_filename, 'wb') as f:
                f.write(img_response.content)
            
            # Upload to GCS
            gcs_path = f"character_sheet/pose_{pose['id']:02d}.png"
            upload_to_gcs(local_filename, 'bass-ic-refs', gcs_path)
            
            generated_poses.append({
                "id": pose['id'],
                "name": pose['name'],
                "description": pose['description'],
                "gcs_path": f"gs://bass-ic-refs/{gcs_path}",
                "local_path": local_filename
            })
            
            print(f"  ✓ Success\n")
            
        except Exception as e:
            print(f"  ✗ Error: {e}\n")
            continue
    
    # Save metadata
    metadata = {
        "character_name": "Bass",
        "character_description": BASE_CHARACTER,
        "style": "SpongeBob SquarePants",
        "total_poses": len(generated_poses),
        "poses": generated_poses,
        "version": "1.0",
        "generated_date": "2025-12-28"
    }
    
    metadata_path = 'character_output/character_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    upload_to_gcs(metadata_path, 'bass-ic-refs', 'metadata/character_metadata.json')
    
    print(f"\n✅ Character sheet generation complete!")
    print(f"   Generated: {len(generated_poses)}/20 poses")
    print(f"   Location: gs://bass-ic-refs/character_sheet/")
    print(f"   Metadata: gs://bass-ic-refs/metadata/character_metadata.json")

if __name__ == "__main__":
    main()
