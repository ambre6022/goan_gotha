import os
from werkzeug.utils import secure_filename
from config.config import Config

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_file(file, user_id):
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{user_id}_{file.filename}")
        file_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(file_path)
        return filename
    return None

def validate_animal_data(data):
    required_fields = ['name', 'type', 'breed', 'age']
    return all(data.get(field) for field in required_fields)