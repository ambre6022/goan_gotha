from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging
from utils.socket_handler import send_alert, emit_vaccination_reminder
from contextlib import contextmanager
from utils.db_utils import get_db_connection

logger = logging.getLogger(__name__)
scheduler = None

@contextmanager
def get_safe_db():
    """Thread-safe database connection context manager"""
    conn = get_db_connection('animals.db')
    try:
        yield conn
    finally:
        conn.close()

def init_scheduler(app):
    """Initialize the scheduler with the Flask application"""
    global scheduler
    if scheduler is None:
        scheduler = BackgroundScheduler()
        
        # Add health monitoring job - runs every 5 minutes
        scheduler.add_job(
            func=check_animal_health,
            trigger=CronTrigger(minute='*/5'),
            id='health_monitor',
            name='Monitor animal health metrics',
            replace_existing=True
        )
        
        # Add vaccination check job - runs daily at 9 AM
        scheduler.add_job(
            func=check_vaccinations,
            trigger=CronTrigger(hour=9, minute=0),
            id='vaccination_check',
            name='Check vaccination schedules',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Scheduler started successfully")
    
    return scheduler

def check_animal_health():
    """Check health metrics for all animals"""
    try:
        with get_safe_db() as conn:
            cursor = conn.cursor()
            
            # Get all animals with their latest health metrics
            cursor.execute("""
                SELECT a.id, a.name, hm.temperature, hm.heart_rate, hm.respiratory_rate
                FROM animals a
                LEFT JOIN health_metrics hm ON a.id = hm.animal_id
                WHERE hm.record_date = (
                    SELECT MAX(record_date)
                    FROM health_metrics
                    WHERE animal_id = a.id
                )
            """)
            
            animals = cursor.fetchall()
            
            for animal in animals:
                if not animal['temperature']:
                    continue
                    
                # Check temperature
                if animal['temperature'] > 39.5:
                    send_alert(animal['id'], {
                        'type': 'critical',
                        'animal_name': animal['name'],
                        'message': f'High temperature ({animal["temperature"]} deg C) - immediate veterinary check required'
                    })
                elif animal['temperature'] > 39.0:
                    send_alert(animal['id'], {
                        'type': 'warning',
                        'animal_name': animal['name'],
                        'message': f'Elevated temperature ({animal["temperature"]} deg C) - keep monitoring'
                    })
                
                # Check heart rate if available
                if animal['heart_rate'] and (animal['heart_rate'] < 60 or animal['heart_rate'] > 100):
                    send_alert(animal['id'], {
                        'type': 'warning',
                        'animal_name': animal['name'],
                        'message': f'Abnormal heart rate ({animal["heart_rate"]} bpm) - schedule a check'
                    })
                
                # Check respiratory rate if available
                if animal['respiratory_rate'] and (animal['respiratory_rate'] < 12 or animal['respiratory_rate'] > 36):
                    send_alert(animal['id'], {
                        'type': 'warning',
                        'animal_name': animal['name'],
                        'message': f'Abnormal respiratory rate ({animal["respiratory_rate"]} breaths/min) - schedule a check'
                    })

    except Exception as e:
        logger.error(f"Error checking animal health: {str(e)}")

def check_vaccinations():
    """Check upcoming vaccinations and send reminders"""
    try:
        with get_safe_db() as conn:
            cursor = conn.cursor()
            
            # Get vaccinations due in the next 7 days
            cursor.execute("""
                SELECT a.id, a.name, v.vaccine_name, v.due_date
                FROM animals a
                JOIN vaccinations v ON a.id = v.animal_id
                WHERE date(v.due_date) BETWEEN date('now') 
                AND date('now', '+7 days')
                AND v.status = 'scheduled'
            """)
            
            upcoming = cursor.fetchall()
            
            for vacc in upcoming:
                due_date = datetime.strptime(vacc['due_date'], '%Y-%m-%d').date()
                days_until = (due_date - datetime.now().date()).days
                
                emit_vaccination_reminder(vacc['id'], {
                    'animal_name': vacc['name'],
                    'vaccine': vacc['vaccine_name'],
                    'due_date': vacc['due_date'],
                    'days_until': days_until,
                    'message': f'Vaccination reminder: {vacc["name"]} is scheduled for {vacc["vaccine_name"]} in {days_until} days'
                })

    except Exception as e:
        logger.error(f"Error checking vaccinations: {str(e)}")

def shutdown_scheduler():
    """Shutdown the scheduler"""
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler shut down successfully")
