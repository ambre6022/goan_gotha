import sqlite3
import os
import logging
from flask import g

logger = logging.getLogger(__name__)

def dict_factory(cursor, row):
    """Convert database row objects to a dictionary"""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def get_db_connection(db_name):
    """Get a database connection with thread safety"""
    if not hasattr(g, 'db_connections'):
        g.db_connections = {}
    
    if db_name not in g.db_connections:
        db_path = os.path.join('data', db_name)
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = dict_factory
        g.db_connections[db_name] = conn
        
    return g.db_connections[db_name]

def init_db():
    """Initialize database tables"""
    # Users database initialization
    conn = get_db_connection('users.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            mobile TEXT UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    # Animals database initialization
    conn = get_db_connection('animals.db')
    
    # Create animal table
    conn.execute('''
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
    
    # Create health_metrics table
    conn.execute('''
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
    
    # Create vaccinations table
    conn.execute('''
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

    # Create milk_production table
    conn.execute('''
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
    
    conn.commit()

def close_db_connection(e=None):
    """Close database connections at the end of request"""
    db_connections = getattr(g, 'db_connections', {})
    for conn in db_connections.values():
        conn.close()
    g.db_connections = {}