"""
Flask backend for Bass-ic Finance web UI.
Handles file uploads to Google Cloud Storage.
"""

import os
from flask import Flask, render_template, request, jsonify
from google.cloud import storage
from datetime import datetime
import json

app = Flask(__name__)

# Configuration
PROJECT_ID = os.environ.get("GCP_PROJECT", "manhwa-engine")
SCRIPTS_BUCKET = "bass-ic-scripts"
storage_client = storage.Client(project=PROJECT_ID)

@app.route('/')
def index():
    """Serve the main UI."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads to GCS."""
    try:
        # Get script file (required)
        if 'script' not in request.files:
            return jsonify({'error': 'No script file provided'}), 400
        
        script_file = request.files['script']
        if script_file.filename == '':
            return jsonify({'error': 'No script file selected'}), 400
        
        # Validate JSON
        try:
            script_content = script_file.read()
            script_data = json.loads(script_content)
            script_file.seek(0)  # Reset file pointer
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON file'}), 400
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        episode_title = script_data.get('episode_title', 'untitled').replace(' ', '_')
        script_filename = f"{episode_title}_{timestamp}.json"
        
        # Upload script to GCS
        bucket = storage_client.bucket(SCRIPTS_BUCKET)
        script_blob = bucket.blob(script_filename)
        script_blob.upload_from_file(
            script_file,
            content_type='application/json'
        )
        
        response_data = {
            'success': True,
            'filename': script_filename,
            'script_url': f'gs://{SCRIPTS_BUCKET}/{script_filename}',
            'timestamp': timestamp
        }
        
        # Handle optional style guide
        if 'style' in request.files and request.files['style'].filename != '':
            style_file = request.files['style']
            style_filename = f"style_guide_{timestamp}.txt"
            style_blob = bucket.blob(f"styles/{style_filename}")
            style_blob.upload_from_file(style_file)
            response_data['style_url'] = f'gs://{SCRIPTS_BUCKET}/styles/{style_filename}'
        
        return jsonify(response_data), 200
        
    except Exception as e:
        app.logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
