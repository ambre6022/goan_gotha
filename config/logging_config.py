import os
import logging.config

logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': 'INFO',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/app.log',
            'formatter': 'default',
            'level': 'INFO',
        },
        'socketio': {
            'class': 'logging.FileHandler',
            'filename': 'logs/socketio.log',
            'formatter': 'default',
            'level': 'INFO',
        },
        'health': {
            'class': 'logging.FileHandler',
            'filename': 'logs/health_monitor.log',
            'formatter': 'default',
            'level': 'INFO',
        },
        'requests': {
            'class': 'logging.FileHandler',
            'filename': 'logs/requests.log',
            'formatter': 'default',
            'level': 'INFO',
        },
        'scheduler': {
            'class': 'logging.FileHandler',
            'filename': 'logs/scheduler.log',
            'formatter': 'default',
            'level': 'INFO',
        }
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'socketio': {
            'handlers': ['socketio'],
            'level': 'INFO',
            'propagate': False,
        },
        'health_monitor': {
            'handlers': ['health'],
            'level': 'INFO',
            'propagate': False,
        },
        'requests': {
            'handlers': ['requests'],
            'level': 'INFO',
            'propagate': False,
        },
        'scheduler': {
            'handlers': ['scheduler'],
            'level': 'INFO',
            'propagate': False,
        }
    }
}

def setup_logging():
    """Configure logging for the application"""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Update log file paths with absolute paths
    for handler in logging_config['handlers'].values():
        if 'filename' in handler:
            handler['filename'] = os.path.join(log_dir, os.path.basename(handler['filename']))

    logging.config.dictConfig(logging_config)