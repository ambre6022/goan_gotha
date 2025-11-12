from flask_socketio import SocketIO, emit, join_room, leave_room
import logging
from datetime import datetime
import eventlet
from utils.db_utils import get_db_connection
from contextlib import contextmanager

logger = logging.getLogger(__name__)
socketio = SocketIO()

def init_socketio(app):
    """Initialize SocketIO with the Flask application"""
    socketio.init_app(app, async_mode='eventlet', cors_allowed_origins="*")
    
    @socketio.on('connect')
    def handle_connect():
        logger.info("Client connected")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info("Client disconnected")
    
    @socketio.on('join')
    def on_join(data):
        animal_id = data.get('animal_id')
        if animal_id:
            join_animal_room(animal_id)
    
    @socketio.on('leave')
    def on_leave(data):
        animal_id = data.get('animal_id')
        if animal_id:
            leave_animal_room(animal_id)
    
    return socketio

@contextmanager
def get_safe_db():
    """Thread-safe database connection context manager"""
    conn = get_db_connection('animals.db')
    try:
        yield conn
    finally:
        conn.close()

def send_alert(animal_id, alert_data):
    """Send an alert to specific animal's room."""
    try:
        room = f"animal_{animal_id}"
        alert_data['timestamp'] = datetime.now().isoformat()
        socketio.emit('alert', alert_data, to=room)
        logger.info(f"Alert sent to room {room}")
    except Exception as e:
        logger.error(f"Error sending alert: {str(e)}")

def broadcast_emergency(alert_data):
    """Broadcast emergency alert to all connected clients."""
    try:
        alert_data['timestamp'] = datetime.now().isoformat()
        socketio.emit('emergency', alert_data, namespace='/')
        logger.info("Emergency broadcast sent")
    except Exception as e:
        logger.error(f"Error broadcasting emergency: {str(e)}")

def join_animal_room(animal_id):
    """Join a specific animal's notification room."""
    try:
        room = f"animal_{animal_id}"
        join_room(room)
        logger.info(f"Client joined room {room}")
    except Exception as e:
        logger.error(f"Error joining room: {str(e)}")

def leave_animal_room(animal_id):
    """Leave a specific animal's notification room."""
    try:
        room = f"animal_{animal_id}"
        leave_room(room)
        logger.info(f"Client left room {room}")
    except Exception as e:
        logger.error(f"Error leaving room: {str(e)}")

def emit_health_update(animal_id, health_data):
    """Emit health update for a specific animal."""
    try:
        room = f"animal_{animal_id}"
        socketio.emit('health_update', health_data, to=room)
        logger.info(f"Health update sent to room {room}")
    except Exception as e:
        logger.error(f"Error sending health update: {str(e)}")

def emit_vaccination_reminder(animal_id, vaccine_data):
    """Emit vaccination reminder for a specific animal."""
    try:
        room = f"animal_{animal_id}"
        socketio.emit('vaccination_reminder', vaccine_data, to=room)
        logger.info(f"Vaccination reminder sent to room {room}")
    except Exception as e:
        logger.error(f"Error sending vaccination reminder: {str(e)}")