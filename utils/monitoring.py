from utils.db_utils import get_db_connection
from utils.event_bus import event_bus
from utils.socket_handler import send_alert, broadcast_emergency
import logging
from datetime import datetime
from config.config import Config
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@contextmanager
def get_safe_db():
    """Thread-safe database connection context manager"""
    conn = get_db_connection('animals.db')
    try:
        yield conn
    finally:
        conn.close()

def check_health_metrics():
    """Monitor animal health metrics and emit alerts if needed"""
    try:
        with get_safe_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT hm.animal_id, a.name, hm.temperature, hm.heart_rate, 
                       hm.activity_level, hm.last_checkup, hm.respiratory_rate
                FROM health_metrics hm
                JOIN animals a ON hm.animal_id = a.id 
                WHERE datetime(hm.last_updated) >= datetime('now', '-1 hour')
            """)
            recent_metrics = cursor.fetchall()
        
        for metric in recent_metrics:
            alerts = []
            
            # Check temperature
            if metric['temperature'] > Config.TEMPERATURE_HIGH:
                alerts.append({
                    'type': 'temperature',
                    'status': 'urgent',
                    'message': f'High temperature: {metric["temperature"]} deg C',
                    'value': metric['temperature']
                })
            elif metric['temperature'] < Config.TEMPERATURE_LOW:
                alerts.append({
                    'type': 'temperature',
                    'status': 'warning',
                    'message': f'Low temperature: {metric["temperature"]} deg C',
                    'value': metric['temperature']
                })
            
            # Check heart rate
            if metric['heart_rate'] > Config.HEART_RATE_CRITICAL:
                alerts.append({
                    'type': 'heart_rate',
                    'status': 'urgent',
                    'message': f'High heart rate: {metric["heart_rate"]} BPM',
                    'value': metric['heart_rate']
                })
            elif metric['heart_rate'] > Config.HEART_RATE_WARNING:
                alerts.append({
                    'type': 'heart_rate',
                    'status': 'warning',
                    'message': f'Elevated heart rate: {metric["heart_rate"]} BPM',
                    'value': metric['heart_rate']
                })
            
            # Check activity level
            if metric['activity_level'] < Config.ACTIVITY_LOW:
                alerts.append({
                    'type': 'activity',
                    'status': 'warning',
                    'message': f'Low activity level: {metric["activity_level"]}%',
                    'value': metric['activity_level']
                })

            # Send alerts
            if alerts:
                # Send individual alerts
                for alert in alerts:
                    if alert['status'] == 'urgent':
                        broadcast_emergency({
                            'animal_id': metric['animal_id'],
                            'animal_name': metric['name'],
                            **alert
                        })
                    else:
                        send_alert(metric['animal_id'], {
                            'animal_name': metric['name'],
                            **alert
                        })
                
                # Record alerts in database
                with get_safe_db() as conn:
                    cursor = conn.cursor()
                    for alert in alerts:
                        cursor.execute("""
                            INSERT INTO health_alerts 
                            (animal_id, alert_type, status, message, value, timestamp)
                            VALUES (?, ?, ?, ?, ?, datetime('now'))
                        """, (
                            metric['animal_id'],
                            alert['type'],
                            alert['status'],
                            alert['message'],
                            alert['value']
                        ))
                    conn.commit()

            # Check last checkup
            if metric['last_checkup']:
                last_checkup = datetime.strptime(metric['last_checkup'], '%Y-%m-%d')
                days_since = (datetime.now() - last_checkup).days
                
                if days_since > Config.CHECKUP_REMINDER_DAYS:
                    send_alert(metric['animal_id'], {
                        'type': 'checkup',
                        'status': 'reminder',
                        'animal_name': metric['name'],
                        'message': f'Afternoon check reminder: last inspection was {days_since} days ago',
                        'last_checkup': metric['last_checkup']
                    })

    except Exception as e:
        logger.error(f"Error monitoring health metrics: {str(e)}")

@event_bus.subscribe('health_alert')
def log_health_alert(data):
    """Log health alerts for record keeping"""
    try:
        logger.warning(
            f"Health alert for animal {data['animal_id']}: "
            f"{data['message']} ({data['status']})"
        )
    except Exception as e:
        logger.error(f"Error logging health alert: {str(e)}")
