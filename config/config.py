import os
import logging

class Config:
    # Basic Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-2025'
    DEBUG = True
    
    # Database Configuration
    DB_PATH = 'sqlite:///data/'
    POOL_SIZE = 5
    MAX_OVERFLOW = 10
    
    # Socket Configuration
    SOCKET_PING_INTERVAL = 25
    SOCKET_PING_TIMEOUT = 120
    
    # Health Monitoring Thresholds
    TEMPERATURE_HIGH = 39.5  # deg C
    TEMPERATURE_LOW = 37.5   # deg C
    HEART_RATE_CRITICAL = 100  # BPM
    HEART_RATE_WARNING = 85   # BPM
    ACTIVITY_LOW = 30         # % of normal
    CHECKUP_REMINDER_DAYS = 30  # Days
    MILK_PRODUCTION_WARNING = 20  # % below average
    
    # Session Configuration
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes
    
    # Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'static/images/animals'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}