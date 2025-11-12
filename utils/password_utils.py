from werkzeug.security import generate_password_hash, check_password_hash

def hash_password(password):
    """Generate a secure hash of the password"""
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return check_password_hash(password_hash, password)

def validate_password_strength(password):
    """Validate password strength
    Returns (bool, str) tuple - (is_valid, error_message)
    """
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
        
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
        
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
        
    return True, ""