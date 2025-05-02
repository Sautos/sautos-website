from flask_login import UserMixin
from datetime import datetime

# Note: db will be passed from app.py to avoid circular imports
def init_models(db):
    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password = db.Column(db.String(128), nullable=False)
        name = db.Column(db.String(100), nullable=False)
        is_admin = db.Column(db.Boolean, default=False)
        bookings = db.relationship('Booking', backref='user', lazy=True)
        testimonials = db.relationship('Testimonial', backref='user', lazy=True)

    class Booking(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        date = db.Column(db.DateTime, nullable=False)
        service = db.Column(db.String(100), nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

    class Testimonial(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        content = db.Column(db.Text, nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

    return User, Booking, Testimonial