from flask import session
from app import create_app, db
from app.models.models import User

# Create Flask app context
app = create_app()
with app.app_context():
    # Clear all session data for all users
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess.clear()
    
    print("All sessions cleared. You should now be able to login with different users in different tabs/browsers.")
    print("Please restart your Flask server after running this script.")

