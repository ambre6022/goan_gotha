from flask import request, jsonify, session, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from app import app
from config.database import get_db_connection
from utils.password_utils import hash_password, verify_password, validate_password_strength
from utils.session import initialize_session, validate_session, end_session, get_current_user_id
import sqlite3

STATUS_SEVERITY = {'Critical': 0, 'Moderate': 1, 'Healthy': 2}


def degrade_status(current_status: str, candidate_status: str) -> str:
    """Return the more severe of the two statuses based on STATUS_SEVERITY."""
    current_rank = STATUS_SEVERITY.get(current_status, STATUS_SEVERITY['Healthy'])
    candidate_rank = STATUS_SEVERITY.get(candidate_status, STATUS_SEVERITY['Healthy'])
    return current_status if current_rank <= candidate_rank else candidate_status

class LoginForm(FlaskForm):
    email = StringField('Email')
    mobile = StringField('Mobile')
    password = PasswordField('Password')

class SignupForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[Email()])
    mobile = StringField('Mobile', validators=[Length(min=10, max=10)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])

@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Always render login page on GET; allow switching accounts even if already logged in
    form = LoginForm()
    signup_form = SignupForm()
    
    if form.validate_on_submit():
        email = form.email.data
        mobile = form.mobile.data
        password = form.password.data
        
        try:
            conn = get_db_connection('users.db')
            cursor = conn.cursor()
            
            if email:
                cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            else:
                cursor.execute('SELECT * FROM users WHERE mobile = ?', (mobile,))
                
            user = cursor.fetchone()
            
            if not user:
                flash('No account found with these credentials', 'error')
            elif not verify_password(password, user['password']):
                flash('Incorrect password', 'error')
            else:
                initialize_session(user['id'])
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard', user_id=user['id']))
                
        except sqlite3.Error as e:
            flash('A database error occurred. Please try again.', 'error')
            print(f"Database error during login: {str(e)}")  # Log the actual error
        finally:
            conn.close()
            
    return render_template('login.html', form=form, signup_form=signup_form)

@app.route('/signup', methods=['POST'])
def signup():
    form = SignupForm()
    
    if form.validate_on_submit():
        try:
            conn = get_db_connection('users.db')
            cursor = conn.cursor()
            
            # Check if email or mobile already exists
            cursor.execute('SELECT * FROM users WHERE email = ? OR mobile = ?', 
                         (form.email.data, form.mobile.data))
            
            if cursor.fetchone():
                flash('Email or mobile number already registered', 'error')
            else:
                # Hash the password before storing
                password_hash = hash_password(form.password.data)
                
                # Insert new user
                cursor.execute('''
                    INSERT INTO users (name, email, mobile, password)
                    VALUES (?, ?, ?, ?)
                ''', (form.name.data, form.email.data, form.mobile.data, password_hash))
                
                conn.commit()
                flash('Registration successful! Please login.', 'success')
            
        except sqlite3.Error as e:
            print(f"Database error during signup: {str(e)}")  # Add logging
            flash('Registration error occurred', 'error')
        finally:
            conn.close()
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return redirect(url_for('login'))

@app.route('/dashboard/<int:user_id>')
def dashboard(user_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        flash('Please login to continue', 'error')
        return redirect(url_for('login'))
    if current_user_id != user_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_id=user_id, active_page='dashboard')

@app.route('/cattle_management/<int:user_id>')
def cattle_management(user_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        flash('Please login to continue', 'error')
        return redirect(url_for('login'))
    if current_user_id != user_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
        
    try:
        conn = get_db_connection('animals.db')
        cursor = conn.cursor()
        
        # Fetch all animals for the current user
        cursor.execute('''
            SELECT *, 
                CASE 
                    WHEN type IN ('Cow', 'Buffalo') AND milk_production > 0 THEN 1 
                    ELSE 0 
                END as is_milking,
                CASE 
                    WHEN category = 'Pregnant' OR pregnancy_cycle > 0 THEN 1 
                    ELSE 0 
                END as is_pregnant
            FROM animal 
            WHERE user_id = ?
        ''', (current_user_id,))
        animals = cursor.fetchall()
        
        # Calculate counts
        total_count = len(animals)
        healthy_count = sum(1 for a in animals if a.get('health_status', 'healthy') == 'healthy')
        milking_count = sum(1 for a in animals if a.get('is_milking', 0) == 1)
        alert_count = sum(1 for a in animals if a.get('health_status') == 'critical')
        pregnant_count = sum(1 for a in animals if a.get('is_pregnant', 0) == 1)
        calves_count = sum(1 for a in animals if a.get('age', 0) < 12)  # Less than 12 months
        
        return render_template('cattle_management.html',
            user_id=user_id,
            animals=animals,
            total_count=total_count,
            healthy_count=healthy_count,
            milking_count=milking_count,
            alert_count=alert_count,
            pregnant_count=pregnant_count,
            calves_count=calves_count,
            active_page='cattle'
        )
    except sqlite3.Error as e:
        flash('Error loading animals', 'error')
        return render_template('cattle_management.html',
            user_id=user_id,
            animals=[],
            total_count=0,
            healthy_count=0,
            milking_count=0,
            alert_count=0,
            pregnant_count=0,
            calves_count=0,
            active_page='cattle'
        )
    finally:
        conn.close()

@app.route('/agro_intelligence/<int:user_id>')
def agro_intelligence(user_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        flash('Please login to continue', 'error')
        return redirect(url_for('login'))
    if current_user_id != user_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    return render_template('agro_intelligence.html', user_id=user_id, active_page='agro')

@app.route('/financial_hub/<int:user_id>')
def financial_hub(user_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        flash('Please login to continue', 'error')
        return redirect(url_for('login'))
    if current_user_id != user_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    return render_template('financial_hub.html', user_id=user_id, active_page='financial')

@app.route('/irrigation/<int:user_id>')
def irrigation(user_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        flash('Please login to continue', 'error')
        return redirect(url_for('login'))
    if current_user_id != user_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    return render_template('Irrigation.html', user_id=user_id, active_page='irrigation')

@app.route('/crop_advisor/<int:user_id>')
def crop_advisor(user_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        flash('Please login to continue', 'error')
        return redirect(url_for('login'))
    if current_user_id != user_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    return render_template('crop_advisor.html', user_id=user_id, active_page='crop')

@app.route('/marketplace/<int:user_id>')
def marketplace(user_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        flash('Please login to continue', 'error')
        return redirect(url_for('login'))
    if current_user_id != user_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    return render_template('marketplace.html', user_id=user_id, active_page='marketplace')

@app.route('/predict_chara/<int:user_id>')
def predict_chara(user_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        flash('Please login to continue', 'error')
        return redirect(url_for('login'))
    if current_user_id != user_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    return render_template('predict_chara.html', user_id=user_id, active_page='fodder')

@app.route('/setting/<int:user_id>')
def setting(user_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        flash('Please login to continue', 'error')
        return redirect(url_for('login'))
    if current_user_id != user_id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('login'))
    return render_template('setting.html', user_id=user_id, active_page='settings')

@app.route('/logout')
def logout():
    end_session()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error=404), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error=500), 500

# Add before_request handler for session validation
@app.before_request
def before_request():
    if not request.endpoint:
        return
        
    # Skip session validation for public routes
    public_routes = ['login', 'signup', 'static', 'home']
    if request.endpoint in public_routes:
        return
        
    # Validate session for all other routes
    if not validate_session():
        flash('Your session has expired. Please login again.', 'error')
        return redirect(url_for('login'))

@app.route('/add_new_cattle', methods=['GET', 'POST'])
def add_new_cattle():
    if request.method == 'POST':
        try:
            user_id = get_current_user_id()
            if not user_id:
                flash('Please login to continue', 'error')
                return redirect(url_for('login'))
                
            # Get form data
            name = request.form.get('name')
            animal_type = request.form.get('type')
            breed = request.form.get('breed')
            age = request.form.get('age')
            weight = request.form.get('weight')
            milk_production = request.form.get('milk_production', 0)
            pregnancy_cycle = request.form.get('pregnancy_cycle', 0)
            has_horns = request.form.get('has_horns') == 'yes'
            category = request.form.get('cow_category')
            use_purpose = request.form.get('use_purpose')
            
            # Handle photo upload
            photo = request.files.get('photo')
            image_filename = None
            if photo:
                # Ensure filename is secure
                filename = secure_filename(photo.filename)
                # Generate unique filename
                image_filename = f"{uuid.uuid4()}_{filename}"
                # Save file
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], 'animals', image_filename))
            
            conn = get_db_connection('animals.db')
            cursor = conn.cursor()
            
            # Insert new animal
            cursor.execute('''
                INSERT INTO animal (
                    user_id, name, type, breed, age, weight, 
                    milk_production, pregnancy_cycle, has_horns,
                    category, use_purpose, image_filename
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, name, animal_type, breed, age, weight,
                milk_production, pregnancy_cycle, has_horns,
                category, use_purpose, image_filename
            ))
            
            conn.commit()
            flash('Animal added successfully', 'success')
            return redirect(url_for('cattle_management', user_id=user_id))
            
        except Exception as e:
            flash(f'Error adding animal: {str(e)}', 'error')
            return redirect(url_for('add_new_cattle'))
        finally:
            conn.close()
            
    return render_template('add_new_cattle.html')

# Route to handle the form submission for registering a new animal
@app.route('/register_animal', methods=['POST'])
def register_animal():
    current_user_id = get_current_user_id()
    if not current_user_id:
        flash('Please login to continue', 'error')
        return redirect(url_for('login'))
        
    try:
        form_data = request.form
        photo = request.files.get('photo')
        conn = get_db_connection('animals.db')
        cursor = conn.cursor()
        
        # Handle custom name if provided
        name = form_data.get('custom_name') if form_data.get('name') == 'other' else form_data.get('name')
        
        # Save photo if provided
        image_filename = None
        if photo and photo.filename:
            # Check if file is allowed
            from utils.helpers import allowed_file, save_file
            if allowed_file(photo.filename):
                image_filename = save_file(photo, current_user_id)
            else:
                flash('Only PNG, JPG, JPEG, GIF or WEBP files are accepted', 'error')
                return redirect(url_for('add_new_cattle'))
        
        # Convert numeric fields
        try:
            age = int(form_data.get('age', 0))
            weight = float(form_data.get('weight', 0))
            milk_production = float(form_data.get('milk_production', 0))
            pregnancy_cycle = int(form_data.get('pregnancy_cycle', 0))
        except ValueError:
            flash('Please enter age and weight as numbers', 'error')
            return redirect(url_for('add_new_cattle'))

        # Handle category based on animal type
        category = None
        if form_data.get('type') == 'Cow':
            category = form_data.get('cow_category')
        
        # Handle use purpose for ox
        use_purpose = None
        if form_data.get('type') == 'Ox':
            use_purpose = form_data.get('custom_use_purpose') if form_data.get('use_purpose') == 'Other' else form_data.get('use_purpose')
        
        cursor.execute('''
            INSERT INTO animal (
                user_id, name, type, breed, age, weight,
                milk_production, pregnancy_cycle, has_horns,
                category, use_purpose, image_filename
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_user_id,
            name,
            form_data.get('type'),
            form_data.get('breed'),
            age,
            weight,
            milk_production,
            pregnancy_cycle,
            1 if form_data.get('has_horns') == 'yes' else 0,
            category,
            use_purpose,
            image_filename
        ))
        
        conn.commit()
        flash('Animal registered successfully', 'success')
        return redirect(url_for('cattle_management', user_id=current_user_id))
        
    except sqlite3.Error as e:
        flash('Error occurred while registering the animal', 'error')
        return redirect(url_for('add_new_cattle'))
    finally:
        conn.close()

@app.route('/api/animals/<int:animal_id>/health', methods=['GET'])
def get_animal_health(animal_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    try:
        conn = get_db_connection('animals.db')
        cursor = conn.cursor()
        
        # Get latest health metrics and animal type
        cursor.execute('''
            SELECT hm.*, a.type, a.weight, a.milk_production
            FROM health_metrics hm
            JOIN animal a ON hm.animal_id = a.id
            WHERE hm.animal_id = ? AND a.user_id = ?
            ORDER BY hm.record_date DESC
            LIMIT 1
        ''', (animal_id, current_user_id))
        
        result = cursor.fetchone()
        
        if result:
            # Define normal ranges for different animal types
            normal_ranges = {
                'Cow': {'temp': (37.5, 39.5), 'heart': (48, 84), 'resp': (26, 50), 'milk_min': 15},
                'Buffalo': {'temp': (37.2, 38.5), 'heart': (40, 60), 'resp': (20, 30), 'milk_min': 10},
                'Goat': {'temp': (38.5, 40.0), 'heart': (70, 90), 'resp': (15, 30), 'milk_min': 2},
                'Sheep': {'temp': (38.3, 39.9), 'heart': (70, 80), 'resp': (16, 34), 'milk_min': 0.5},
                'Ox': {'temp': (37.5, 39.5), 'heart': (40, 70), 'resp': (20, 40), 'weight_min': 300},
                'Bull': {'temp': (37.5, 39.5), 'heart': (40, 70), 'resp': (20, 40), 'weight_min': 300}
            }
            
            animal_type = result['type']
            ranges = normal_ranges.get(animal_type, normal_ranges['Cow'])
            
            # Calculate overall status based on animal type
            status = 'Healthy'
            alerts = []
            
            # Temperature check
            if result['temperature']:
                if result['temperature'] > ranges['temp'][1]:
                    status = 'Critical'
                    alerts.append('High temperature')
                elif result['temperature'] > ranges['temp'][1] - 0.5:
                    status = 'Moderate'
                    alerts.append('Slightly elevated temperature')
                    
            # Heart rate check
            if result['heart_rate']:
                if result['heart_rate'] > ranges['heart'][1]:
                    alerts.append('High heart rate')
                    status = degrade_status(status, 'Moderate')
                elif result['heart_rate'] < ranges['heart'][0]:
                    alerts.append('Low heart rate')
                    status = degrade_status(status, 'Moderate')
                    
            # Weight/Production check
            if animal_type in ['Cow', 'Buffalo', 'Goat', 'Sheep']:
                if result['milk_production'] and result['milk_production'] < ranges['milk_min']:
                    alerts.append('Low milk production')
                    status = degrade_status(status, 'Moderate')
            elif animal_type in ['Ox', 'Bull']:
                if result['weight'] and result['weight'] < ranges['weight_min']:
                    alerts.append('Low weight')
                    status = degrade_status(status, 'Moderate')
            
            health_data = {
                'temperature': result['temperature'],
                'heart_rate': result['heart_rate'],
                'respiratory_rate': result['respiratory_rate'],
                'weight': result['weight'],
                'overall_status': status,
                'alerts': alerts,
                'record_date': result['record_date']
            }
            
            # Get vaccination info
            cursor.execute('''
                SELECT vaccine_name, date_given, next_due_date
                FROM vaccinations 
                WHERE animal_id = ?
                ORDER BY date_given DESC 
                LIMIT 1
            ''', (animal_id,))
            
            vacc = cursor.fetchone()
            if vacc:
                health_data.update({
                    'last_vaccine': vacc['vaccine_name'],
                    'vaccine_date': vacc['date_given'],
                    'next_vaccine_due': vacc['next_due_date']
                })
            
            return jsonify({
                'success': True,
                'data': health_data
            })
        else:
            return jsonify({
                'success': True,
                'data': {
                    'temperature': None,
                    'heart_rate': None,
                    'respiratory_rate': None,
                    'weight': None,
                    'overall_status': 'Healthy',
                    'alerts': []
                }
            })
        
    except sqlite3.Error as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        conn.close()

@app.route('/api/animals/<int:animal_id>/card')
def get_animal_card(animal_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    try:
        conn = get_db_connection('animals.db')
        cursor = conn.cursor()
        
        # Get animal details with health and vaccination info
        cursor.execute('''
            SELECT a.*, 
                   hm.temperature as last_temp,
                   hm.record_date as last_checkup,
                   v.next_due_date as next_vaccination,
                   v.vaccine_name,
                    CASE 
                        WHEN hm.temperature > 39.5 THEN 'Critical'
                        WHEN hm.temperature > 39.0 THEN 'Moderate'
                        ELSE 'Optimal'
                    END as health_status
            FROM animal a
            LEFT JOIN health_metrics hm ON a.id = hm.animal_id
            LEFT JOIN vaccinations v ON a.id = v.animal_id
            WHERE a.id = ? AND a.user_id = ?
            ORDER BY hm.record_date DESC, v.date_given DESC
            LIMIT 1
        ''', (animal_id, current_user_id))
        
        animal = cursor.fetchone()
        if not animal:
            flash('Animal not found', 'error')
            return redirect(url_for('cattle_management', user_id=current_user_id))
            
        return render_template('animal_card.html', animal=animal)
        
    except sqlite3.Error as e:
        flash('Error loading animal details', 'error')
        return redirect(url_for('cattle_management', user_id=current_user_id))
    finally:
        conn.close()

@app.route('/api/animals/<int:animal_id>/qr')
def get_animal_qr(animal_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    try:
        conn = get_db_connection('animals.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM animal WHERE id = ? AND user_id = ?', (animal_id, current_user_id))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Animal not found'}), 404

        # Generate QR code with animal details URL
        base_url = request.url_root.rstrip('/')
        qr_data = f"{base_url}/api/animals/{animal_id}/card"
        
        import qrcode
        import io
        import base64
        
        # Create QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Convert to base64
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered)
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({'success': True, 'qr_code': qr_base64})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/animals/<int:animal_id>', methods=['DELETE'])
def delete_animal(animal_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    try:
        conn = get_db_connection('animals.db')
        cursor = conn.cursor()
        
        # Verify animal belongs to current user
        cursor.execute('SELECT id FROM animal WHERE id = ? AND user_id = ?', (animal_id, current_user_id))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Animal not found'}), 404

        # Delete all related records first
        cursor.execute('DELETE FROM health_metrics WHERE animal_id = ?', (animal_id,))
        cursor.execute('DELETE FROM vaccinations WHERE animal_id = ?', (animal_id,))
        cursor.execute('DELETE FROM milk_production WHERE animal_id = ?', (animal_id,))
        
        # Finally delete the animal record
        cursor.execute('DELETE FROM animal WHERE id = ? AND user_id = ?', (animal_id, current_user_id))
        
        conn.commit()
        return jsonify({'success': True})
        
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/animals/<int:animal_id>', methods=['PUT'])
def update_animal(animal_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    try:
        conn = get_db_connection('animals.db')
        cursor = conn.cursor()
        
        # Verify animal belongs to current user
        cursor.execute('SELECT id FROM animal WHERE id = ? AND user_id = ?', (animal_id, current_user_id))
        if not cursor.fetchone():
            return jsonify({'success': False, 'error': 'Animal not found'}), 404

        form_data = request.get_json()
        
        cursor.execute('''
            UPDATE animal SET
                name = ?,
                type = ?,
                breed = ?,
                age = ?,
                weight = ?,
                milk_production = ?,
                pregnancy_cycle = ?,
                has_horns = ?,
                category = ?,
                use_purpose = ?
            WHERE id = ? AND user_id = ?
        ''', (
            form_data.get('name'),
            form_data.get('type'),
            form_data.get('breed'),
            form_data.get('age'),
            form_data.get('weight'),
            form_data.get('milk_production', 0),
            form_data.get('pregnancy_cycle', 0),
            1 if form_data.get('has_horns') else 0,
            form_data.get('category'),
            form_data.get('use_purpose'),
            animal_id,
            current_user_id
        ))
        
        conn.commit()
        return jsonify({'success': True})
        
    except sqlite3.Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/animals/<int:animal_id>', methods=['GET'])
def get_animal(animal_id):
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    try:
        conn = get_db_connection('animals.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM animal 
            WHERE id = ? AND user_id = ?
        ''', (animal_id, current_user_id))
        
        animal = cursor.fetchone()
        if not animal:
            return jsonify({'success': False, 'error': 'Animal not found'}), 404
            
        # Convert row to dict
        animal_dict = dict(animal)
        return jsonify({'success': True, 'data': animal_dict})
        
    except sqlite3.Error as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/animals', methods=['GET'])
def get_all_animals():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    try:
        conn = get_db_connection('animals.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, 
                   hm.temperature as last_temp,
                   hm.record_date as last_checkup,
                   mp.amount as milk_production,
                   v.next_due_date as next_vaccination
            FROM animal a
            LEFT JOIN health_metrics hm ON a.id = hm.animal_id
            LEFT JOIN (
                SELECT animal_id, amount
                FROM milk_production
                WHERE (animal_id, record_date) IN (
                    SELECT animal_id, MAX(record_date)
                    FROM milk_production
                    GROUP BY animal_id
                )
            ) mp ON a.id = mp.animal_id
            LEFT JOIN vaccinations v ON a.id = v.animal_id
            WHERE a.user_id = ?
            GROUP BY a.id
        ''', (current_user_id,))
        
        animals = cursor.fetchall()
        animal_list = []
        
        for animal in animals:
            animal_dict = dict(animal)
            # Add image URL if exists
            if animal_dict.get('image_filename'):
                animal_dict['image_url'] = f"/static/images/animals/{animal_dict['image_filename']}"
            animal_list.append(animal_dict)
            
        return jsonify({
            'success': True,
            'animals': animal_list
        })
        
    except sqlite3.Error as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        conn.close()
