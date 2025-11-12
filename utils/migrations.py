from utils.db_utils import execute_write
import logging
import os
from config.database import get_db_connection

logger = logging.getLogger(__name__)

def run_migrations():
    """Run all database migrations"""
    try:
        # Initialize users database
        execute_write('users.db', '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                mobile TEXT UNIQUE,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Initialize animals database tables
        execute_write('animals.db', '''
            CREATE TABLE IF NOT EXISTS animal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                breed TEXT NOT NULL,
                age INTEGER,
                weight REAL,
                milk_production REAL DEFAULT 0,
                pregnancy_cycle INTEGER DEFAULT 0,
                has_horns INTEGER DEFAULT 0,
                category TEXT,
                use_purpose TEXT,
                photo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        execute_write('animals.db', '''
            CREATE TABLE IF NOT EXISTS health_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                animal_id INTEGER NOT NULL,
                temperature REAL,
                heart_rate INTEGER,
                respiratory_rate INTEGER,
                weight REAL,
                body_condition_score INTEGER,
                record_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (animal_id) REFERENCES animal (id)
            )
        ''')

        execute_write('animals.db', '''
            CREATE TABLE IF NOT EXISTS vaccinations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                animal_id INTEGER NOT NULL,
                vaccine_name TEXT NOT NULL,
                date_given DATE NOT NULL,
                next_due_date DATE,
                vet_name TEXT,
                notes TEXT,
                FOREIGN KEY (animal_id) REFERENCES animal (id)
            )
        ''')

        execute_write('animals.db', '''
            CREATE TABLE IF NOT EXISTS milk_production (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                animal_id INTEGER NOT NULL,
                production_date DATE NOT NULL,
                amount REAL NOT NULL,
                time_of_day TEXT CHECK(time_of_day IN ('morning', 'evening')) NOT NULL,
                fat_content REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES animal (id)
            )
        ''')
        
        logger.info("Database migrations completed successfully")
        
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}")
        raise