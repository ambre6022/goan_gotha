from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta
import threading
import time

class RateLimiter:
    def __init__(self, max_requests=5, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # IP: list of timestamps
        self._cleanup_thread = threading.Thread(target=self._cleanup_old_requests, daemon=True)
        self._cleanup_thread.start()
    
    def is_rate_limited(self, ip):
        now = datetime.now()
        if ip not in self.requests:
            self.requests[ip] = []
        
        # Remove old requests
        self.requests[ip] = [ts for ts in self.requests[ip] 
                           if now - ts < timedelta(seconds=self.window_seconds)]
        
        # Check if too many requests
        if len(self.requests[ip]) >= self.max_requests:
            return True
        
        # Add new request
        self.requests[ip].append(now)
        return False
    
    def _cleanup_old_requests(self):
        while True:
            now = datetime.now()
            for ip in list(self.requests.keys()):
                self.requests[ip] = [ts for ts in self.requests[ip] 
                                   if now - ts < timedelta(seconds=self.window_seconds)]
                if not self.requests[ip]:
                    del self.requests[ip]
            time.sleep(60)  # Cleanup every minute

# Create a global rate limiter instance
limiter = RateLimiter()

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        if limiter.is_rate_limited(ip):
            return jsonify({
                'error': 'Too many requests. Please try again later.'
            }), 429
        return f(*args, **kwargs)
    return decorated_function
