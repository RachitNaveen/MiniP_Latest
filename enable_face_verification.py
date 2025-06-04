from app import create_app, db
from app.models.models import User

app = create_app()

with app.app_context():
    username_to_update = "tshreek"
    user = User.query.filter_by(username=username_to_update).first()

    if user:
        user.face_verification_enabled = True
        db.session.commit()
        print(f"Face verification enabled for user: {user.username}")
    else:
        print(f"User '{username_to_update}' not found.")
