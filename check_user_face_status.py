from app import create_app, db
from app.models.models import User

app = create_app()

with app.app_context():
    username_to_check = "tshreek"
    print("[DEBUG] Querying database for user...")
    user = User.query.filter_by(username=username_to_check).first()
    print("[DEBUG] Query complete.")

    if user:
        print(f"User: {user.username}")
        print(f"  Face Verification Enabled: {user.face_verification_enabled}")
        if user.face_data:
            print(f"  Face Data Stored: Yes")
            try:
                import json
                face_data_json = json.loads(user.face_data)
                if 'encoding' in face_data_json and face_data_json['encoding']:
                    print(f"  Face Encoding Present: Yes")
                else:
                    print(f"  Face Encoding Present: No (or empty)")
            except Exception as e:
                print(f"  Face Data Stored: Yes, but error parsing: {e}")
        else:
            print(f"  Face Data Stored: No")
    else:
        print(f"User '{username_to_check}' not found.")

