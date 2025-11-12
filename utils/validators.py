import re
from typing import Optional, Tuple

def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format"
    return True, "Email is valid"

def validate_mobile(mobile: str) -> Tuple[bool, str]:
    """Validate Indian mobile number."""
    pattern = r'^[6-9]\d{9}$'
    if not re.match(pattern, mobile):
        return False, "Invalid mobile number"
    return True, "Mobile number is valid"

def validate_animal_data(data: dict, file=None) -> tuple[bool, str | None]:
    """Validate animal registration data."""
    required_fields = {
        'type': 'Type is required',
        'name': 'Name is required',
        'breed': 'Breed is required',
        'age': 'Age is required'
    }

    # Check required fields
    for field, message in required_fields.items():
        if not data.get(field):
            return False, message

    # Validate age
    try:
        age = int(data.get('age', 0))
        if age <= 0 or age > 300:  # 25 years in months
            return False, "Age must be between 0 and 300 months"
    except ValueError:
        return False, "Age must be numeric"

    # Validate weight if provided
    if data.get('weight'):
        try:
            weight = float(data['weight'])
            if weight <= 0 or weight > 2000:  # Max 2000 kg
                return False, "Weight must be between 0 and 2000 kilograms"
        except ValueError:
            return False, "Weight must be numeric"

    # Validate milk production if provided
    if data.get('milk_production'):
        try:
            milk = float(data['milk_production'])
            if milk < 0 or milk > 100:  # Max 100 liters per day
                return False, "Milk production must be between 0 and 100 liters"
        except ValueError:
            return False, "Milk production must be numeric"

    # Validate pregnancy cycle if provided
    if data.get('pregnancy_cycle'):
        try:
            cycle = int(data['pregnancy_cycle'])
            if cycle < 0 or cycle > 12:  # Max 12 months
                return False, "Pregnancy cycle must be between 0 and 12 months"
        except ValueError:
            return False, "Pregnancy cycle must be numeric"

    # Validate photo if provided
    if file and file.filename:
        # Check file size (max 5MB)
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
        if len(file.read()) > MAX_FILE_SIZE:
            return False, "Photo must not exceed 5MB"
        
        # Reset file pointer after reading
        file.seek(0)
        
        # Check file extension
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not '.' in file.filename or \
           file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return False, "Only PNG, JPG, JPEG, GIF or WEBP files are accepted"

    return True, None

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS."""
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    # Convert special characters to HTML entities
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    return text

def validate_file_extension(filename: str) -> bool:
    """Validate allowed file extensions."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS