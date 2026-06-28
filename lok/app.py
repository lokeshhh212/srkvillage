from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# ===== APP CONFIGURATION =====
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///village_portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ===== INITIALIZE EXTENSIONS =====
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

# ===== DATABASE MODELS =====
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    contact = db.Column(db.String(50), nullable=True)
    is_emergency = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False)
    is_important = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(50), default='Pending')
    date = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# ===== CREATE ADMIN USER =====
def create_admin():
    with app.app_context():
        db.create_all()
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = Admin(username='admin', password_hash=hashed_password)
            db.session.add(admin)
            db.session.commit()
            print('✅ Admin user created!')
            print('📝 Username: admin')
            print('🔑 Password: admin123')

# ===== ROUTES =====

@app.route('/')
def index():
    services = Service.query.all()
    events = Event.query.all()
    announcements = Announcement.query.all()
    complaints = Complaint.query.all()
    return render_template('index.html', 
                         services=services, 
                         events=events, 
                         announcements=announcements,
                         complaints=complaints)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and bcrypt.check_password_hash(admin.password_hash, password):
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    services = Service.query.all()
    events = Event.query.all()
    announcements = Announcement.query.all()
    complaints = Complaint.query.all()
    
    stats = {
        'services': len(services),
        'events': len(events),
        'announcements': len(announcements),
        'complaints': len(complaints),
        'pending_complaints': Complaint.query.filter_by(status='Pending').count()
    }
    
    return render_template('admin_dashboard.html', 
                         services=services,
                         events=events,
                         announcements=announcements,
                         complaints=complaints,
                         stats=stats)

# ===== API ROUTES FOR CRUD OPERATIONS =====

# --- SERVICES ---
@app.route('/api/services', methods=['POST'])
@login_required
def add_service():
    data = request.json
    service = Service(
        title=data['title'],
        description=data['description'],
        contact=data.get('contact', ''),
        is_emergency=data.get('is_emergency', False)
    )
    db.session.add(service)
    db.session.commit()
    return jsonify({'success': True, 'id': service.id})

@app.route('/api/services/<int:id>', methods=['GET'])
@login_required
def get_service(id):
    service = Service.query.get_or_404(id)
    return jsonify({
        'id': service.id,
        'title': service.title,
        'description': service.description,
        'contact': service.contact,
        'is_emergency': service.is_emergency
    })

@app.route('/api/services/<int:id>', methods=['PUT'])
@login_required
def update_service(id):
    service = Service.query.get_or_404(id)
    data = request.json
    service.title = data['title']
    service.description = data['description']
    service.contact = data.get('contact', '')
    service.is_emergency = data.get('is_emergency', False)
    service.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/services/<int:id>', methods=['DELETE'])
@login_required
def delete_service(id):
    service = Service.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    return jsonify({'success': True})

# --- EVENTS ---
@app.route('/api/events', methods=['POST'])
@login_required
def add_event():
    data = request.json
    event = Event(
        title=data['title'],
        description=data['description'],
        date=data['date'],
        location=data.get('location', '')
    )
    db.session.add(event)
    db.session.commit()
    return jsonify({'success': True, 'id': event.id})

@app.route('/api/events/<int:id>', methods=['GET'])
@login_required
def get_event(id):
    event = Event.query.get_or_404(id)
    return jsonify({
        'id': event.id,
        'title': event.title,
        'description': event.description,
        'date': event.date,
        'location': event.location
    })

@app.route('/api/events/<int:id>', methods=['PUT'])
@login_required
def update_event(id):
    event = Event.query.get_or_404(id)
    data = request.json
    event.title = data['title']
    event.description = data['description']
    event.date = data['date']
    event.location = data.get('location', '')
    event.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/events/<int:id>', methods=['DELETE'])
@login_required
def delete_event(id):
    event = Event.query.get_or_404(id)
    db.session.delete(event)
    db.session.commit()
    return jsonify({'success': True})

# --- ANNOUNCEMENTS ---
@app.route('/api/announcements', methods=['POST'])
@login_required
def add_announcement():
    data = request.json
    announcement = Announcement(
        title=data['title'],
        content=data['content'],
        date=data['date'],
        is_important=data.get('is_important', False)
    )
    db.session.add(announcement)
    db.session.commit()
    return jsonify({'success': True, 'id': announcement.id})

@app.route('/api/announcements/<int:id>', methods=['GET'])
@login_required
def get_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    return jsonify({
        'id': announcement.id,
        'title': announcement.title,
        'content': announcement.content,
        'date': announcement.date,
        'is_important': announcement.is_important
    })

@app.route('/api/announcements/<int:id>', methods=['PUT'])
@login_required
def update_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    data = request.json
    announcement.title = data['title']
    announcement.content = data['content']
    announcement.date = data['date']
    announcement.is_important = data.get('is_important', False)
    announcement.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/announcements/<int:id>', methods=['DELETE'])
@login_required
def delete_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    db.session.delete(announcement)
    db.session.commit()
    return jsonify({'success': True})

# --- COMPLAINTS ---
@app.route('/api/complaints', methods=['POST'])
@login_required
def add_complaint():
    data = request.json
    complaint = Complaint(
        title=data['title'],
        description=data['description'],
        location=data.get('location', ''),
        status=data.get('status', 'Pending'),
        date=datetime.utcnow().strftime('%Y-%m-%d')
    )
    db.session.add(complaint)
    db.session.commit()
    return jsonify({'success': True, 'id': complaint.id})

@app.route('/api/complaints/<int:id>', methods=['GET'])
@login_required
def get_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    return jsonify({
        'id': complaint.id,
        'title': complaint.title,
        'description': complaint.description,
        'location': complaint.location,
        'status': complaint.status,
        'date': complaint.date
    })

@app.route('/api/complaints/<int:id>', methods=['PUT'])
@login_required
def update_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    data = request.json
    complaint.title = data['title']
    complaint.description = data['description']
    complaint.location = data.get('location', '')
    complaint.status = data['status']
    complaint.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/complaints/<int:id>', methods=['DELETE'])
@login_required
def delete_complaint(id):
    complaint = Complaint.query.get_or_404(id)
    db.session.delete(complaint)
    db.session.commit()
    return jsonify({'success': True})
# Add this import at the top if not already there
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
# ... other imports ...

# ===== ADD THIS NEW ROUTE =====
@app.route('/api/public/complaints', methods=['POST'])
def public_add_complaint():
    """Allow public to submit complaints without login"""
    try:
        data = request.json
        complaint = Complaint(
            title=data['title'],
            description=data['description'],
            location=data.get('location', ''),
            status='Pending',
            date=datetime.utcnow().strftime('%Y-%m-%d')
        )
        db.session.add(complaint)
        db.session.commit()
        return jsonify({'success': True, 'id': complaint.id, 'message': 'Complaint submitted successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

if __name__ == '__main__':
    create_admin()
    print('\n🚀 Starting Village Information Portal...')
    print('📍 Visit: http://localhost:5000')
    print('🔐 Admin Login: http://localhost:5000/admin/login')
    print('=' * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)