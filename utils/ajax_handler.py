from functools import wraps
from flask import jsonify, request, session
from flask_wtf.csrf import generate_csrf
from werkzeug.security import safe_str_cmp

def handle_ajax_error(error_msg, status_code=400):
    """Standardized error response for AJAX requests"""
    return jsonify({
        'success': False,
        'error': error_msg
    }), status_code

def ajax_response(data=None, message=None, status_code=200):
    """Standardized success response for AJAX requests"""
    response = {
        'success': True,
        'data': data or {},
    }
    if message:
        response['message'] = message
    return jsonify(response), status_code

def validate_ajax_request(required_fields=None):
    """Validate AJAX request data"""
    if not request.is_json:
        return False, 'Invalid content type'
    
    data = request.get_json()
    if required_fields:
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return False, f'Missing required fields: {", ".join(missing_fields)}'
    
    return True, data

def validate_ajax_token():
    """Validate CSRF token for AJAX requests"""
    token = request.headers.get('X-CSRF-Token')
    if not token or not safe_str_cmp(token, generate_csrf()):
        return False
    return True

def csrf_protected(f):
    """Decorator to enforce CSRF protection on AJAX endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not validate_ajax_token():
            return handle_ajax_error('Invalid CSRF token', 403)
        return f(*args, **kwargs)
    return decorated_function

# Update existing ajax_login_required to include CSRF protection
def ajax_login_required(f):
    """Decorator for AJAX endpoints that require authentication and CSRF protection"""
    @wraps(f)
    @csrf_protected
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function