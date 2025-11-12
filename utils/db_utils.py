import sqlite3
import logging
from config.database import get_db_connection

logger = logging.getLogger(__name__)

def execute_query(db_name, query, params=()):
    """Execute a database query with proper error handling"""
    try:
        conn = get_db_connection(db_name)
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Database error executing query: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        raise

def execute_write(db_name, query, params=()):
    """Execute a write operation with proper error handling"""
    try:
        conn = get_db_connection(db_name)
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Database error executing write: {str(e)}")
        conn.rollback()
        raise
    except Exception as e:
        logger.error(f"Error executing write: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        raise

def execute_many(db_name, query, params_list):
    """Execute many write operations in a single transaction"""
    try:
        conn = get_db_connection(db_name)
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database error executing batch write: {str(e)}")
        conn.rollback()
        raise
    except Exception as e:
        logger.error(f"Error executing batch write: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        raise