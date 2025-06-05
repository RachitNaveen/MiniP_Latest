"""
Test script for face verification modal functionality.
This script creates a simple test page to verify that the face modal is working correctly.
"""

from flask import Flask, render_template, jsonify, request
import logging

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

if __name__ == '__main__':
    app.run(debug=True, port=5001)
