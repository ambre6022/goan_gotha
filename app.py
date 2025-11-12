from flask import Flask
from flask_wtf.csrf import CSRFProtect
from config.database import init_db
import threading
import webbrowser

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
csrf = CSRFProtect(app)

# Initialize database
with app.app_context():
    init_db()


# Import routes after app is created to avoid circular imports
from routes import *

if __name__ == '__main__':
    def _open_browser():
        try:
            webbrowser.open_new('http://127.0.0.1:5000/')
        except Exception:
            # Fail silently if a browser cannot be opened
            pass

    threading.Timer(1.0, _open_browser).start()
    app.run(debug=True)
