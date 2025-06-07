from app import create_app, db
from app.models.models import User
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_db():
    app = create_app()
    with app.app_context():
        logger.info("Dropping all tables...")
        db.drop_all()
        
        logger.info("Creating all tables...")
        db.create_all()
        
        logger.info("Database initialized successfully!")

if __name__ == '__main__':
    init_db()
