from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from config import Config
from flask_migrate import Migrate
import os

# Custom Flask class that modifies the session cookie name based on URL parameter
class CustomFlask(Flask):
    def process_response(self, response):
        # Get the user_id parameter from the URL
        user_id = request.args.get('user_id')
        if user_id:
            # Set a custom session cookie name based on the user_id
            self.config['SESSION_COOKIE_NAME'] = f'session_{user_id}'
        return super().process_response(response)

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = CustomFlask(__name__)
    app.config.from_object(config_class)
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
    app.config['FACE_VERIFICATION_REQUIRED'] = True
    app.config['SESSION_COOKIE_NAME'] = 'securechat_session'  # Use a consistent session name

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)  # Initialize Flask-Migrate
    socketio.init_app(app, cors_allowed_origins="*", async_mode="threading")
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'main.login'

    # Ensure instance and upload folders exist
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    os.makedirs(os.path.join(app.static_folder, 'face-api-models'), exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'uploads'), exist_ok=True)

    with app.app_context():
        from app.routes import routes
        from app.routes import socket_events
        from app.models.models import User
        from app.auth.auth import auth_blueprint
        from app.security.routes_security import security_blueprint

        # Register the blueprint
        app.register_blueprint(routes.bp)
        # Register the auth blueprint
        app.register_blueprint(auth_blueprint, url_prefix='/auth')
        # Register the security blueprint
        app.register_blueprint(security_blueprint, url_prefix='/security')
        # Register the face blueprint
        from app.auth.routes_face import face_blueprint
        app.register_blueprint(face_blueprint, url_prefix='/face')

        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

        db.create_all()

    return app
