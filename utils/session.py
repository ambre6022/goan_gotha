from flask import session
from datetime import datetime, timedelta

SESSION_TIMEOUT = 3600  # 1 hour in seconds

def initialize_session(user_id):
    """Initialize a secure session with timeout"""
    session.clear()  # Clear any existing session data
    session.permanent = True
    session['user_id'] = user_id
    session['login_time'] = datetime.utcnow().timestamp()
    session['last_activity'] = datetime.utcnow().timestamp()
    session['csrf_token_expiry'] = (datetime.utcnow() + timedelta(hours=24)).timestamp()

def validate_session():
    """Validate session and handle timeouts"""
    if 'user_id' not in session:
        return False

    current_time = datetime.utcnow().timestamp()
    
    # Check for session timeout
    if current_time - session.get('last_activity', 0) > SESSION_TIMEOUT:
        session.clear()
        return False
    
    # Update last activity
    session['last_activity'] = current_time
    return True

def end_session():
    """Securely end the session"""
    session.clear()

def get_current_user_id():
    """Get the current user ID from session"""
    return session.get('user_id') if validate_session() else None