#!/usr/bin/env python
from app import create_app, db
from app.models.models import User

def check_face_users():
    app = create_app()
    with app.app_context():
        face_users = User.query.filter(User.face_verification_enabled == True).all()
        print(f'Found {len(face_users)} users with face verification enabled:')
        for user in face_users:
            print(f' - {user.username}')
        
        if len(face_users) == 0:
            # Let's create a test user with face verification
            print("No users with face verification found.")
            print("Creating a test user with face verification...")
            import os
            if os.path.exists('create_face_user.py'):
                os.system('python create_face_user.py')
            else:
                print("Could not find create_face_user.py script")

if __name__ == "__main__":
    check_face_users()
