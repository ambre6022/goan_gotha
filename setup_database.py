from app import app
from config.database import init_db
import logging

logger = logging.getLogger(__name__)

def setup_database():
    """Initialize all database tables"""
    try:
        with app.app_context():
            init_db()
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        raise

if __name__ == "__main__":
    setup_database()