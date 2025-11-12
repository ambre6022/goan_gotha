from flask import Flask
from flask_wtf.csrf import CSRFProtect
from config.database import init_db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
csrf = CSRFProtect(app)

# Initialize database
with app.app_context():
    init_db()


# Import routes after app is created to avoid circular imports
from routes import *

if __name__ == '__main__':
    app.run(debug=True)