"""
Notification Service for Bass-ic Finance Automation.
Handles Slack notifications and serves as a centralized notifier.
"""

import os
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Environment variables
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

@app.route('/notify', methods=['POST'])
def send_notification():
    """
    Send a notification to Slack.
    Expected JSON:
    {
        "title": "Video Ready",
        "message": "Episode 1 is complete.",
        "video_url": "https://...",
        "status": "success"  # or 'error'
    }
    """
    if not SLACK_WEBHOOK_URL:
        # If no webhook is configured, just log it (soft fail)
        print("⚠️  No SLACK_WEBHOOK_URL configured. Skipping notification.")
        return jsonify({"status": "skipped", "reason": "no_webhook"}), 200

    data = request.json
    title = data.get("title", "Notification")
    message = data.get("message", "")
    video_url = data.get("video_url")
    status = data.get("status", "info")

    # Build Slack payload (Block Kit)
    color = "#36a64f" if status == "success" else "#ff0000"
    emoji = "✅" if status == "success" else "❌"
    
    slack_payload = {
        "text": f"{emoji} {title}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {title}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]
    }

    if video_url:
        slack_payload["blocks"].append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Drive Link:*\n{video_url}"
            }
        })
    
    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=slack_payload,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        print(f"✅ Notification sent to Slack. Status: {response.status_code}")
        return jsonify({"status": "sent"}), 200
        
    except Exception as e:
        print(f"❌ Failed to send notification: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
