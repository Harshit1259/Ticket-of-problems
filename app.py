from flask import Flask, render_template, request, jsonify, session, flash, redirect, url_for
from models import db, Ticket
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tickets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Hardcoded users
REPORTERS = ['Alice', 'Bob']
ADMINS = ['Admin1', 'Admin2']

def current_user():
    """Helper function to get current user from session"""
    name = session.get('user_name', 'Alice')
    role = session.get('user_role', 'Reporter')
    return {'name': name, 'role': role}

def is_admin():
    """Check if current user is admin"""
    return current_user()['role'] == 'Admin'

def is_reporter():
    """Check if current user is reporter"""
    return current_user()['role'] == 'Reporter'

def validate_ticket_data(data):
    """Validate ticket data and return errors if any"""
    errors = []
    
    # Title validation
    title = data.get('title', '').strip()
    if not title:
        errors.append('Title is required')
    elif len(title) < 3 or len(title) > 120:
        errors.append('Title must be between 3 and 120 characters')
    
    # Description validation
    description = data.get('description', '').strip()
    if not description:
        errors.append('Description is required')
    elif len(description) < 1 or len(description) > 1000:
        errors.append('Description must be between 1 and 1000 characters')
    
    # Priority validation
    priority = data.get('priority', '')
    if priority not in Ticket.valid_priorities():
        errors.append(f'Priority must be one of: {", ".join(Ticket.valid_priorities())}')
    
    return errors

# UI Routes
@app.route('/')
def index():
    """Main page - list tickets with filters"""
    status_filter = request.args.get('status', '')
    admin_filter = request.args.get('assigned_admin', '')
    
    query = Ticket.query
    
    if status_filter:
        query = query.filter(Ticket.status == status_filter)
    if admin_filter:
        query = query.filter(Ticket.assigned_admin == admin_filter)
    
    tickets = query.order_by(Ticket.created_at.desc()).all()
    
    # Get counts by status
    status_counts = {}
    for status in Ticket.valid_statuses():
        count = Ticket.query.filter_by(status=status).count()
        status_counts[status] = count
    
    return render_template('index.html', 
                         tickets=tickets, 
                         status_counts=status_counts,
                         current_user=current_user(),
                         reporters=REPORTERS,
                         admins=ADMINS)

@app.route('/new_ticket')
def new_ticket():
    """New ticket form page"""
    if not is_reporter():
        flash('Only reporters can create tickets', 'error')
        return redirect(url_for('index'))
    return render_template('new_ticket.html', current_user=current_user())

@app.route('/admin')
def admin():
    """Admin dashboard page"""
    if not is_admin():
        flash('Only admins can access admin dashboard', 'error')
        return redirect(url_for('index'))
    
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    return render_template('admin.html', 
                         tickets=tickets, 
                         current_user=current_user(),
                         reporters=REPORTERS,
                         admins=ADMINS)

@app.route('/set_role', methods=['POST'])
def set_role():
    """Set user role in session"""
    user_name = request.form.get('user_name')
    user_role = request.form.get('user_role')
    
    # Validate the combination
    if user_role == 'Reporter' and user_name in REPORTERS:
        session['user_name'] = user_name
        session['user_role'] = 'Reporter'
    elif user_role == 'Admin' and user_name in ADMINS:
        session['user_name'] = user_name
        session['user_role'] = 'Admin'
    else:
        # If invalid combination, set to a valid default
        if user_role == 'Admin':
            session['user_name'] = 'Admin1'  # Default admin
            session['user_role'] = 'Admin'
        elif user_role == 'Reporter':
            session['user_name'] = 'Alice'   # Default reporter
            session['user_role'] = 'Reporter'
        else:
            flash('Invalid user or role', 'error')
    
    return redirect(url_for('index'))

# API Routes
@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    """Get tickets with optional filters"""
    status_filter = request.args.get('status', '')
    admin_filter = request.args.get('assigned_admin', '')
    
    query = Ticket.query
    
    if status_filter:
        query = query.filter(Ticket.status == status_filter)
    if admin_filter:
        query = query.filter(Ticket.assigned_admin == admin_filter)
    
    tickets = query.order_by(Ticket.created_at.desc()).all()
    return jsonify([ticket.to_dict() for ticket in tickets])

@app.route('/api/tickets', methods=['POST'])
def create_ticket():
    """Create a new ticket (reporter only)"""
    if not is_reporter():
        return jsonify({'errors': ['Only reporters can create tickets']}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'errors': ['No data provided']}), 400
    
    errors = validate_ticket_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    try:
        ticket = Ticket(
            title=data['title'],
            description=data['description'],
            priority=data['priority'],
            reporter_name=current_user()['name']
        )
        db.session.add(ticket)
        db.session.commit()
        
        return jsonify(ticket.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'errors': ['Failed to create ticket']}), 500

@app.route('/api/tickets/<int:ticket_id>/assign-self', methods=['PATCH'])
def assign_self(ticket_id):
    """Assign ticket to current admin"""
    if not is_admin():
        return jsonify({'errors': ['Only admins can assign tickets']}), 403
    
    ticket = Ticket.query.get_or_404(ticket_id)
    
    if ticket.assigned_admin:
        return jsonify({'errors': ['Ticket is already assigned']}), 400
    
    try:
        ticket.assigned_admin = current_user()['name']
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(ticket.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'errors': ['Failed to assign ticket']}), 500

@app.route('/api/tickets/<int:ticket_id>/status', methods=['PATCH'])
def update_status(ticket_id):
    """Update ticket status (admin only)"""
    if not is_admin():
        return jsonify({'errors': ['Only admins can update ticket status']}), 403
    
    ticket = Ticket.query.get_or_404(ticket_id)
    data = request.get_json()
    
    if not data or 'status' not in data:
        return jsonify({'errors': ['Status is required']}), 400
    
    new_status = data['status']
    if new_status not in Ticket.valid_statuses():
        return jsonify({'errors': [f'Status must be one of: {", ".join(Ticket.valid_statuses())}']}), 400
    
    try:
        ticket.status = new_status
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(ticket.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'errors': ['Failed to update ticket status']}), 500

@app.route('/api/tickets/<int:ticket_id>', methods=['DELETE'])
def delete_ticket(ticket_id):
    """Delete a ticket"""
    ticket = Ticket.query.get_or_404(ticket_id)
    
    try:
        db.session.delete(ticket)
        db.session.commit()
        return jsonify({'message': 'Ticket deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'errors': ['Failed to delete ticket']}), 500

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    if request.path.startswith('/api/'):
        return jsonify({'errors': ['Bad request']}), 400
    flash('Bad request', 'error')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'message': 'Resource not found'}), 404
    flash('Page not found', 'error')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({'errors': ['Internal server error']}), 500
    flash('Internal server error', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
