from app import create_app, db, socketio
import os

app = create_app()

if __name__ == '__main__':
    # Ensure the database is created
    with app.app_context():
        db.create_all()

    # Check for face-api.js model files
    face_models_dir = os.path.join(app.static_folder, 'face-api-models')
    if not os.path.exists(face_models_dir) or not os.listdir(face_models_dir):
        print("  Face detection models not found.")
        print(" Download models from:")
        print("   https://github.com/justadudewhohacks/face-api.js/tree/master/weights")
        print(f"   And place them in: {face_models_dir}\n")

    # Import argparse to handle command line arguments
    import argparse
    
    # Create argument parser
    parser = argparse.ArgumentParser(description='Run the SecureChat application')
    parser.add_argument('--port', type=int, default=5000, help='Port number to run the application on')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run with Flask-SocketIO for real-time messaging
    print(f"Starting server on port {args.port}")
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True, host='0.0.0.0', port=args.port)

    # For production with SSL, uncomment and configure:
    # socketio.run(
    #     app,
    #     host='0.0.0.0',
    #     port=443,
    #     debug=False,
    #     ssl_context=(app.config['SSL_CERT'], app.config['SSL_KEY'])
    # )
