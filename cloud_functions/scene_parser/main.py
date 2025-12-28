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

# Use latest Gemini 3 Flash model
model = GenerativeModel("gemini-3-flash-preview")

# Style System Prompts
STYLE_GUIDE = """
STYLE: SpongeBob SquarePants animation style.
- Backgrounds: Organic curved shapes, flower clouds, painterly textures, vibrant but slightly muted underwater palette.
- Character: "Bass" (Fish-like humanoid), yellow-orange head, navy suit.
- Mood: Professional yet whimsical.
"""

def generate_prompts(scene_data):
    """
    Uses Gemini to generate specific image generation prompts from scene descriptions.
    """
    prompt_request = f"""
    You are an expert production designer for a SpongeBob-style animation.
    Convert this scene description into two specific image generation prompts:
    1. background_prompt: For Imagen 3. Describe the environment, lighting, angle, and style. NO CHARACTERS.
    2. character_prompt: For nano-banana-pro. Describe the character 'Bass' (fish humanoid), his pose, expression, and action.
    
    Style Guide: {STYLE_GUIDE}
    
    Scene Input:
    - Visual: {scene_data.get('visual', scene_data.get('scene_description'))}
    - Narration context: {scene_data.get('narration')}
    - Timestamp: {scene_data.get('timestamp')}
    
    Return pure JSON:
    {{
        "background_prompt": "...",
        "character_prompt": "..."
    }}
    """
    
    response = model.generate_content(
        prompt_request,
        generation_config=GenerationConfig(response_mime_type="application/json")
    )
    
    return json.loads(response.text)

@functions_framework.cloud_event
def parse_script_handler(cloud_event):
    """
    Triggered by a file change in the scripts bucket.
    Reads JSON, enriches with prompts, returns processed data.
    """
    data = cloud_event.data
    bucket_name = data["bucket"]
    file_name = data["name"]
    
    print(f"🎬 Processing script: gs://{bucket_name}/{file_name}")
    
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    
    script_content = blob.download_as_text()
    script_json = json.loads(script_content)
    
    processed_scenes = []
    
    # Process each scene
    for idx, scene in enumerate(script_json.get("scenes", [])):
        print(f"  Processing Scene {idx + 1}...")
        
        # If prompts missing, generate them
        if "background_prompt" not in scene or "character_prompt" not in scene:
            prompts = generate_prompts(scene)
            scene.update(prompts)
        
        # Ensure scene number
        scene["scene_number"] = idx + 1
        
        # Add common metadata if missing
        if "pose_id" not in scene:
             # Simple logic: cycle poses or default to neutral for now
             # In a real system, LLM could pick the best pose_id from the list
             scene["pose_id"] = 0 
             
        processed_scenes.append(scene)
    
    # Return result (Antigravity will capture this return value)
    result = {
        "episode_metadata": {
            "title": script_json.get("title"),
            "number": script_json.get("episode_number")
        },
        "scenes": processed_scenes
    }
    
    # In a Cloud Function generic trigger, we might write back to storage or just return.
    # For Antigravity workflow "cloud-function" type, the return value is often captured 
    # if it's an HTTP function. If it's an Event function, we might need to write to a 'processed' bucket.
    # However, the workflow.yaml expects outputs. 
    # NOTE: The workflow definition in step 7 uses "cloud-function" type which typically implies 
    # an HTTP trigger or a specific connector. 
    # BUT the trigger in workflow.yaml is "OBJECT_FINALIZE" which implies Eventarc.
    # For simplicity here, we'll assume the workflow invokes this via HTTP *passing* the bucket/object 
    # OR it's an event trigger that writes to an output that the next step reads.
    
    # Given the workflow.yaml structure:
    # steps:
    # - name: parse-script
    #   outputs: [episode_metadata, scenes]
    
    # This implies an HTTP function that returns JSON is best for the workflow orchestration 
    # to capture outputs directly.
    
    return result

# wrapper for HTTP invocation (if used as HTTP function in workflow)
@functions_framework.http
def parse_script_http(request):
    request_json = request.get_json(silent=True)
    
    # Mock cloud event data structure if called via HTTP with body
    class MockCloudEvent:
        data = request_json
        
    return parse_script_handler(MockCloudEvent)
