"""
Helper functions for the ChatBot Factory platform
"""

import os
import re
import hashlib
import secrets
import string
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
from flask import request, current_app
import logging

def generate_secure_token(length=32):
    """Generate a cryptographically secure random token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_string(text, salt=None):
    """Create a SHA-256 hash of a string with optional salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    combined = f"{text}{salt}"
    hash_object = hashlib.sha256(combined.encode())
    return f"{salt}:{hash_object.hexdigest()}"

def verify_hash(text, hashed_text):
    """Verify a string against its hash"""
    try:
        salt, hash_value = hashed_text.split(':', 1)
        new_hash = hash_string(text, salt)
        return new_hash == hashed_text
    except ValueError:
        return False

def sanitize_filename(filename):
    """Sanitize a filename for safe storage"""
    # Remove any non-alphanumeric characters except dots, hyphens, and underscores
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    return filename

def validate_email(email):
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username format (alphanumeric, underscore, 3-30 chars)"""
    pattern = r'^[a-zA-Z0-9_]{3,30}$'
    return re.match(pattern, username) is not None

def validate_telegram_token(token):
    """Validate Telegram bot token format"""
    pattern = r'^\d+:[A-Za-z0-9_-]{35}$'
    return re.match(pattern, token) is not None

def format_datetime(dt, format_string='%Y-%m-%d %H:%M:%S'):
    """Format datetime object to string"""
    if dt is None:
        return ""
    return dt.strftime(format_string)

def parse_datetime(date_string, format_string='%Y-%m-%d %H:%M:%S'):
    """Parse datetime string to datetime object"""
    try:
        return datetime.strptime(date_string, format_string)
    except (ValueError, TypeError):
        return None

def get_time_ago(dt):
    """Get human-readable time difference from now"""
    if dt is None:
        return "Never"
    
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

def is_safe_url(target):
    """Check if a URL is safe for redirect"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc

def get_client_ip():
    """Get client IP address from request"""
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']

def truncate_text(text, max_length=100, suffix='...'):
    """Truncate text to specified length with suffix"""
    if text is None:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def format_file_size(size_bytes):
    """Format file size in bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def format_number(number):
    """Format number with thousands separators"""
    try:
        return f"{int(number):,}"
    except (ValueError, TypeError):
        return str(number)

def calculate_percentage(part, total):
    """Calculate percentage with safe division"""
    if total == 0:
        return 0
    return round((part / total) * 100, 2)

def get_env_bool(key, default=False):
    """Get boolean environment variable"""
    value = os.environ.get(key, '').lower()
    return value in ('true', '1', 'yes', 'on')

def get_env_int(key, default=0):
    """Get integer environment variable"""
    try:
        return int(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default

def get_env_float(key, default=0.0):
    """Get float environment variable"""
    try:
        return float(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default

def log_user_action(user_id, action, details=None):
    """Log user action for audit purposes"""
    log_data = {
        'user_id': user_id,
        'action': action,
        'timestamp': datetime.utcnow().isoformat(),
        'ip_address': get_client_ip(),
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    }
    
    if details:
        log_data['details'] = details
    
    logging.info(f"User Action: {log_data}")

def clean_html(text):
    """Remove HTML tags from text"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text or '')

def generate_slug(text, max_length=50):
    """Generate URL-friendly slug from text"""
    # Convert to lowercase and replace spaces with hyphens
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    # Truncate if too long
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    return slug

def merge_dicts(*dicts):
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result

def chunk_list(lst, chunk_size):
    """Split list into chunks of specified size"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def remove_duplicates(lst, key=None):
    """Remove duplicates from list while preserving order"""
    if key is None:
        seen = set()
        return [x for x in lst if not (x in seen or seen.add(x))]
    else:
        seen = set()
        return [x for x in lst if not (key(x) in seen or seen.add(key(x)))]

def deep_get(dictionary, keys, default=None):
    """Safely get nested dictionary value"""
    for key in keys:
        if isinstance(dictionary, dict) and key in dictionary:
            dictionary = dictionary[key]
        else:
            return default
    return dictionary

def retry_on_failure(max_retries=3, delay=1):
    """Decorator to retry function on failure"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
            return None
        return wrapper
    return decorator

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = {}
    
    def is_allowed(self, key, max_requests=60, window_seconds=60):
        """Check if request is allowed based on rate limit"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Clean old requests
        if key in self.requests:
            self.requests[key] = [req_time for req_time in self.requests[key] if req_time > window_start]
        else:
            self.requests[key] = []
        
        # Check if under limit
        if len(self.requests[key]) < max_requests:
            self.requests[key].append(now)
            return True
        
        return False

# Global rate limiter instance
rate_limiter = RateLimiter()
