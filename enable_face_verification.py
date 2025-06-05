# Enable face verification for the user
from app import db, create_app
from app.models.models import User
import json

app = create_app()
with app.app_context():
    user = User.query.filter_by(username="tshreek").first()
    
    # Make sure face_verification_enabled is True
    user.face_verification_enabled = True
    
    # Check if face data exists and is valid
    if not user.face_data:
        print("Warning: No face data stored.")
    elif user.face_data:
        try:
            # Validate JSON format
            face_data = json.loads(user.face_data)
            if 'encoding' not in face_data:
                print("Warning: Face data doesn't contain encoding.")
            else:
                print(f"Face data seems valid with {len(face_data['encoding'])} points")
        except:
            print("Warning: Face data is not valid JSON.")
    
    db.session.commit()
    print(f"Updated face verification settings for {user.username}")