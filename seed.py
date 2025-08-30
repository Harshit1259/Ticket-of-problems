#!/usr/bin/env python3
"""
Seed script for Mini Support Ticketing System
Creates database and adds sample tickets for testing
"""

from app import app, db
from models import Ticket
from datetime import datetime

def create_sample_tickets():
    """Create sample tickets for testing"""
    sample_tickets = [
        {
            'title': 'Website login not working',
            'description': 'Users are unable to log in to the website. Getting error 500 when trying to access the login page. This is affecting all users since yesterday.',
            'priority': 'high',
            'status': 'open',
            'reporter_name': 'Alice'
        },
        {
            'title': 'Database connection slow',
            'description': 'Database queries are taking longer than usual. Response times have increased from 100ms to 2-3 seconds. This is impacting user experience.',
            'priority': 'medium',
            'status': 'in_progress',
            'reporter_name': 'Bob',
            'assigned_admin': 'Admin1'
        },
        {
            'title': 'Email notifications not sending',
            'description': 'Users are not receiving email notifications for password resets and account confirmations. SMTP server seems to be down.',
            'priority': 'high',
            'status': 'open',
            'reporter_name': 'Alice'
        },
        {
            'title': 'Mobile app crashes on startup',
            'description': 'The mobile app crashes immediately when opened on iOS devices. Android devices work fine. This started happening after the latest update.',
            'priority': 'medium',
            'status': 'open',
            'reporter_name': 'Bob'
        },
        {
            'title': 'User profile picture upload fails',
            'description': 'Users cannot upload profile pictures. The upload button is not responding and no error message is shown. File size limit is set to 5MB.',
            'priority': 'low',
            'status': 'closed',
            'reporter_name': 'Alice',
            'assigned_admin': 'Admin2'
        }
    ]
    
    for ticket_data in sample_tickets:
        ticket = Ticket(**ticket_data)
        db.session.add(ticket)
    
    try:
        db.session.commit()
        print(f"✅ Created {len(sample_tickets)} sample tickets")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error creating sample tickets: {e}")

def main():
    """Main function to set up database and seed data"""
    with app.app_context():
        print("🚀 Setting up Mini Support Ticketing System...")
        
        # Create all tables
        print("📊 Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully")
        
        # Check if tickets already exist
        existing_tickets = Ticket.query.count()
        if existing_tickets > 0:
            print(f"⚠️  Database already contains {existing_tickets} tickets")
            response = input("Do you want to add sample tickets anyway? (y/N): ")
            if response.lower() != 'y':
                print("📝 Skipping sample ticket creation")
                return
        else:
            print("📝 No existing tickets found")
        
        # Create sample tickets
        print("🎫 Creating sample tickets...")
        create_sample_tickets()
        
        # Display summary
        total_tickets = Ticket.query.count()
        open_tickets = Ticket.query.filter_by(status='open').count()
        in_progress_tickets = Ticket.query.filter_by(status='in_progress').count()
        closed_tickets = Ticket.query.filter_by(status='closed').count()
        
        print("\n📈 Database Summary:")
        print(f"   Total tickets: {total_tickets}")
        print(f"   Open: {open_tickets}")
        print(f"   In Progress: {in_progress_tickets}")
        print(f"   Closed: {closed_tickets}")
        
        print("\n🎉 Setup complete! You can now run the application:")
        print("   flask run")
        print("\n👥 Available users:")
        print("   Reporters: Alice, Bob")
        print("   Admins: Admin1, Admin2")

if __name__ == '__main__':
    main()
