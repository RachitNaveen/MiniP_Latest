"""
Test script for face verification modal functionality.
This script creates a simple test page to verify that the face modal is working correctly.
"""

from flask import Flask, render_template, jsonify, request
import logging
import requests

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

@app.route('/')
def test_page():
    """Renders a simple test page for face modal."""
    return render_template('test_face_modal.html')

@app.route('/mock_unlock_item', methods=['POST'])
def mock_unlock():
    """Mock endpoint for testing face verification."""
    # Simulate server processing time
    import time
    time.sleep(1)
    
    # Return success response
    return jsonify({
        'success': True,
        'content': 'This is the unlocked message content!',
        'fileName': 'test_file.pdf',
        'fileUrl': '/static/sample_file.pdf'
    })

def test_unlock_attempts():
    base_url = "http://localhost:5000/unlock_item"
    headers = {"Content-Type": "application/json"}

    # Simulate 3 unlock attempts
    for i in range(1, 5):
        payload = {
            "itemType": "message",
            "itemId": "test_message_id",
            "cancelled": True
        }
        response = requests.post(base_url, json=payload, headers=headers)
        print(f"Attempt {i}: Status Code: {response.status_code}, Response: {response.json()}")

        if i == 4:
            assert response.status_code == 403, "4th attempt should be forbidden"
            assert response.json().get("message") == "This message has been permanently deleted and cannot be unlocked.", "Message should indicate permanent deletion"

if __name__ == '__main__':
    app.run(debug=True, port=5001)
    test_unlock_attempts()
