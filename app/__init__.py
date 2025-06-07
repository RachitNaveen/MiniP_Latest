from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_wtf.csrf import CSRFProtect
from config import Config
from flask_migrate import Migrate
import os

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'main.login'

    # Import models
    from app.models.models import User
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    # Register blueprints
    from app.routes import routes
    from app.auth.routes_face import face_blueprint
    from app.auth.auth import auth_blueprint
    from app.security.routes_security import security_blueprint
    
    app.register_blueprint(routes.bp)
    app.register_blueprint(face_blueprint, url_prefix='/face')
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(security_blueprint, url_prefix='/security')

    return app