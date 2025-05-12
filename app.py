import sys
import os
import logging
import importlib.util

# Set up logging to print to stderr (visible in Render logs)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log the Python version and sys.path
logger.info(f"Python version: {sys.version}")
logger.info(f"sys.path: {sys.path}")

# Function to load modules using importlib
def load_module(module_name):
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            logger.error(f"importlib.util.find_spec('{module_name}') returned None")
            raise ImportError(f"Cannot find {module_name} module")
        else:
            logger.info(f"Found {module_name} spec: {spec}")
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            logger.info(f"Successfully loaded {module_name} using importlib")
            return sys.modules[module_name]
    except Exception as e:
        logger.error(f"Failed to load {module_name} using importlib: {str(e)}")
        raise

# Load flask_wtf
flask_wtf = load_module("flask_wtf")
FlaskForm = flask_wtf.FlaskForm

# Load flask_sqlalchemy
flask_sqlalchemy = load_module("flask_sqlalchemy")
SQLAlchemy = flask_sqlalchemy.SQLAlchemy

# Load flask_login
flask_login = load_module("flask_login")
LoginManager = flask_login.LoginManager
UserMixin = flask_login.UserMixin
login_user = flask_login.login_user
login_required = flask_login.login_required
logout_user = flask_login.logout_user
current_user = flask_login.current_user

# Load flask_mail
flask_mail = load_module("flask_mail")
Mail = flask_mail.Mail
Message = flask_mail.Message

# Original imports that don't need importlib
from flask import Flask, render_template, request, redirect, url_for, flash
from wtforms import StringField, PasswordField, TextAreaField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sautos_secret_key_2025'

# Use an absolute path for the database URI
base_dir = os.path.abspath(os.path.dirname(__file__))
instance_dir = os.path.join(base_dir, 'instance')
if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)  # Create the instance directory if it doesn't exist
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_dir, "sautos.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SendGrid SMTP configuration via Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True  # Use SSL for port 465
app.config['MAIL_USERNAME'] = 'apikey'
app.config['MAIL_PASSWORD'] = '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'  # Replace with your SendGrid API key
app.config['MAIL_DEFAULT_SENDER'] = ('S-AUTOS', 'info@sautos.net')  # Set "From Name" to "S-AUTOS"

# Initialize Flask-Mail
mail = Mail(app)

# Initialize SQLAlchemy
db = SQLAlchemy()
db.init_app(app)

# Initialize LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Define models directly in app.py to avoid circular imports
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
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Forms
class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class BookingForm(FlaskForm):
    date = DateField('Preferred Date', format='%Y-%m-%d', validators=[DataRequired()])
    service = SelectField('Service', choices=[('Exterior Cleaning', 'Exterior Cleaning'), ('Interior Cleaning', 'Interior Cleaning')], validators=[DataRequired()])
    submit = SubmitField('Book Appointment')

    def validate_date(self, field):
        # Prevent past dates
        if field.data < date.today():
            raise ValidationError('Cannot book a date in the past.')
        # Restrict to Mondays and Saturdays
        weekday = field.data.weekday()
        if weekday not in [0, 5]:  # 0 = Monday, 5 = Saturday
            raise ValidationError('Bookings are only available on Mondays and Saturdays.')

class TestimonialForm(FlaskForm):
    content = TextAreaField('Your Testimonial', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Submit Testimonial')

class EmailForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Send Email')

# Routes
@app.route('/')
def home():
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).limit(3).all()
    return render_template('index.html', testimonials=testimonials)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        flash(f"Thank you, {name}! We've received your message and will get back to you at {email}.", "success")
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/booking', methods=['GET', 'POST'])
@login_required
def booking():
    form = BookingForm()
    if form.validate_on_submit():
        booking = Booking(
            user_id=current_user.id,
            date=form.date.data,
            service=form.service.data,
            status='pending'
        )
        db.session.add(booking)
        db.session.commit()
        
        # Send email to admin for confirmation using Flask-Mail
        try:
            msg = Message(
                subject=f"New Booking Request - {form.service.data}",
                recipients=['sayiddzaurov@gmail.com'],
                body=f"""
                New booking request from {current_user.name} ({current_user.email}):
                
                Date: {form.date.data}
                Service: {form.service.data}
                
                Please confirm this booking via the admin panel.
                """
            )
            mail.send(msg)
            flash(f"Booking request submitted! Awaiting admin confirmation.", "success")
        except Exception as e:
            flash(f"Booking request submitted, but failed to send email notification to admin: {str(e)}", "warning")
        
        return redirect(url_for('dashboard'))
    return render_template('booking.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        user = User(email=form.email.data, password=hashed_password, name=form.name.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('dashboard.html', bookings=bookings)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied: Admins only.', 'error')
        return redirect(url_for('home'))
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    testimonials = Testimonial.query.order_by(Testimonial.created_at.desc()).all()
    if request.method == 'POST':
        if 'delete_testimonial' in request.form:
            testimonial_id = request.form['delete_testimonial']
            testimonial = Testimonial.query.get_or_404(testimonial_id)
            db.session.delete(testimonial)
            db.session.commit()
            flash('Testimonial deleted.', 'success')
        elif 'delete_booking' in request.form:
            booking_id = request.form['delete_booking']
            booking = Booking.query.get_or_404(booking_id)
            db.session.delete(booking)
            db.session.commit()
            flash('Booking deleted.', 'success')
        elif 'confirm_booking' in request.form:
            booking_id = request.form['confirm_booking']
            booking = Booking.query.get_or_404(booking_id)
            booking.status = 'confirmed'
            db.session.commit()
            # Send confirmation email to user
            try:
                msg = Message(
                    subject="Your S-AUTOS Booking is Confirmed",
                    recipients=[booking.user.email],
                    body=f"""
                    Dear {booking.user.name},
                    
                    Your booking for {booking.service} on {booking.date.strftime('%Y-%m-%d')} has been confirmed.
                    
                    We look forward to serving you at S-AUTOS!
                    
                    Best regards,
                    S-AUTOS Team
                    """
                )
                mail.send(msg)
                flash(f'Booking confirmed and email sent to {booking.user.email}.', 'success')
            except Exception as e:
                flash(f'Booking confirmed, but failed to send email: {str(e)}', 'warning')
        elif 'cancel_booking' in request.form:
            booking_id = request.form['cancel_booking']
            booking = Booking.query.get_or_404(booking_id)
            booking.status = 'cancelled'
            db.session.commit()
            # Send cancellation email to user
            try:
                msg = Message(
                    subject="Your S-AUTOS Booking Has Been Cancelled",
                    recipients=[booking.user.email],
                    body=f"""
                    Dear {booking.user.name},
                    
                    Your booking for {booking.service} on {booking.date.strftime('%Y-%m-%d')} has been cancelled.
                    
                    If you have any questions, please contact us.
                    
                    Best regards,
                    S-AUTOS Team
                    """
                )
                mail.send(msg)
                flash(f'Booking cancelled and email sent to {booking.user.email}.', 'success')
            except Exception as e:
                flash(f'Booking cancelled, but failed to send email: {str(e)}', 'warning')
        return redirect(url_for('admin'))
    return render_template('admin.html', bookings=bookings, testimonials=testimonials)

@app.route('/admin/email_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def email_user(user_id):
    if not current_user.is_admin:
        flash('Access denied: Admins only.', 'error')
        return redirect(url_for('home'))
    user = User.query.get_or_404(user_id)
    form = EmailForm()
    if form.validate_on_submit():
        try:
            msg = Message(
                subject=form.subject.data,
                recipients=[user.email],
                body=f"""
                Dear {user.name},
                
                {form.message.data}
                
                Best regards,
                S-AUTOS Team
                """
            )
            mail.send(msg)
            flash(f'Email sent to {user.email}.', 'success')
        except Exception as e:
            flash(f'Failed to send email: {str(e)}', 'error')
        return redirect(url_for('admin'))
    return render_template('email_user.html', form=form, user=user)

@app.route('/submit_testimonial', methods=['GET', 'POST'])
@login_required
def submit_testimonial():
    form = TestimonialForm()
    if form.validate_on_submit():
        testimonial = Testimonial(
            user_id=current_user.id,
            content=form.content.data
        )
        db.session.add(testimonial)
        db.session.commit()
        flash('Thank you for your testimonial!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('submit_testimonial.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

# Initialize database
with app.app_context():
    db.create_all()
    # Create an admin user if none exists
    if not User.query.filter_by(email='admin@sautos.com').first():
        admin = User(
            email='admin@sautos.com',
            password=generate_password_hash('admin123', method='pbkdf2:sha256'),
            name='Admin',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)