from functools import wraps
from utils.socket_handler import socketio
import logging
from threading import Lock

logger = logging.getLogger(__name__)
event_handlers = {}
lock = Lock()

def init_event_bus(app):
    """Initialize the event bus system"""
    logger.info("Initializing event bus")
    return EventBus()

class EventBus:
    @staticmethod
    def subscribe(event_type):
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                return f(*args, **kwargs)
            with lock:
                if event_type not in event_handlers:
                    event_handlers[event_type] = []
                event_handlers[event_type].append(wrapped)
            return wrapped
        return decorator

    @staticmethod
    def emit(event_type, data, room=None):
        """Emit an event to all subscribers and through socket.io if applicable"""
        try:
            # Handle socket.io events
            if room:
                socketio.emit(event_type, data, room=room)
            else:
                socketio.emit(event_type, data)

            # Handle local event subscribers
            if event_type in event_handlers:
                with lock:
                    handlers = event_handlers[event_type].copy()
                for handler in handlers:
                    try:
                        handler(data)
                    except Exception as e:
                        logger.error(f"Error in event handler for {event_type}: {str(e)}")

        except Exception as e:
            logger.error(f"Error emitting event {event_type}: {str(e)}")

    @staticmethod
    def remove_handler(event_type, handler):
        """Remove a specific event handler"""
        with lock:
            if event_type in event_handlers:
                try:
                    event_handlers[event_type].remove(handler)
                except ValueError:
                    pass