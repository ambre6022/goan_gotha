from utils.db_utils import execute_query, execute_write
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)

def add_sample_milk_data():
    """Add sample milk production data for testing"""
    try:
        # Get all cow IDs
        cows = execute_query('animals.db', "SELECT id FROM animal WHERE type = 'Cow'")
        
        # Add milk production records for the last 7 days
        today = datetime.now()
        for cow in cows:
            for i in range(7):
                date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
                
                # Morning milk (higher production)
                morning_amount = round(random.uniform(8.0, 15.0), 2)
                morning_fat = round(random.uniform(3.0, 5.0), 2)
                execute_write('animals.db', '''
                    INSERT INTO milk_production (
                        animal_id, production_date, amount, 
                        time_of_day, fat_content
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (cow['id'], date, morning_amount, 'morning', morning_fat))
                
                # Evening milk (lower production)
                evening_amount = round(random.uniform(6.0, 12.0), 2)
                evening_fat = round(random.uniform(3.0, 5.0), 2)
                execute_write('animals.db', '''
                    INSERT INTO milk_production (
                        animal_id, production_date, amount, 
                        time_of_day, fat_content
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (cow['id'], date, evening_amount, 'evening', evening_fat))
                
                # Update total milk production for the cow
                execute_write('animals.db', '''
                    UPDATE animal 
                    SET milk_production = (
                        SELECT SUM(amount) 
                        FROM milk_production 
                        WHERE animal_id = ? AND production_date = ?
                    )
                    WHERE id = ?
                ''', (cow['id'], date, cow['id']))
        
        logger.info("Sample milk production data added successfully")
        
    except Exception as e:
        logger.error(f"Error adding sample milk data: {str(e)}")
        raise

if __name__ == '__main__':
    add_sample_milk_data()