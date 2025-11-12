from functools import wraps
from flask import request, g
import time
import logging
from datetime import datetime

def setup_request_logging(app):
    """Setup request logging for the application"""
    if not app.debug:
        file_handler = logging.FileHandler('logs/requests.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('Request Logger Startup')

def log_request(f):
    """Decorator to log request details"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.start_time = time.time()
        
        # Log request details
        request_data = {
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'path': request.path,
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'user_id': g.get('user_id', None)
        }
        
        response = f(*args, **kwargs)
        
        # Log response details
        duration = time.time() - g.start_time
        status_code = response.status_code if hasattr(response, 'status_code') else 200
        
        log_message = (
            f"Request: {request_data['method']} {request_data['path']} | "
            f"Status: {status_code} | "
            f"Duration: {duration:.2f}s | "
            f"IP: {request_data['ip']} | "
            f"User ID: {request_data['user_id']}"
        )
        
        if 200 <= status_code < 400:
            logging.getLogger('request').info(log_message)
        else:
            logging.getLogger('request').warning(log_message)
        
        return response
    return decorated_function