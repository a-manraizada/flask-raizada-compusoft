from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import urllib.parse
import pandas as pd
import os
from werkzeug.security import generate_password_hash, check_password_hash

# app = Flask(__name__)
app = Flask(__name__, instance_path='/tmp/flask_instance')
app.secret_key = 'super secret key'
db_password = 'Aman@2791'
db_password = urllib.parse.quote_plus(db_password)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://postgres.hpokpmcaqjjlaigoczmh:{db_password}@aws-0-ap-south-1.pooler.supabase.com:6543/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
db = SQLAlchemy(app)


# Create a simple model
class CallingData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(100))
    status = db.Column(db.String(100))
    remarks = db.Column(db.String(100))
    called_by = db.Column(db.String(100))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Initialize DB
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    return render_template('dashboard.html', username=session['name'])

@app.route('/about')
def about():
    return 'About'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('User already exists.', 'warning')
            return redirect(url_for('register'))

        new_user = User(name=name, email=email, username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('User registered successfully.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['name'] = user.name
            session['role'] = user.role
            session['user_name'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Clears all session data
    flash('Logged out successfully.', 'info')  # Optional feedback
    return redirect(url_for('login'))  # Redirect to login or home

import traceback

@app.route('/users')
def users():
    all_users = User.query.all()
    return render_template('users.html', users=all_users)

@app.route('/upload', methods=['GET', 'POST'])
def upload_data():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied. Admins only.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file part.', 'danger')
                return redirect(url_for('upload_data'))

            file = request.files['file']
            if file.filename == '':
                flash('No file selected.', 'warning')
                return redirect(url_for('upload_data'))

            if file and file.filename.endswith('.xlsx'):
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)

                df = pd.read_excel(filepath)
                for _, row in df.iterrows():
                    entry = CallingData(
                        phone_number=str(row['phone_number']),
                        status="to call",
                        called_by="",
                        remarks=""
                    )
                    db.session.add(entry)
                db.session.commit()

                flash('Data uploaded successfully!', 'success')
            else:
                flash('Invalid file type. Please upload a .xlsx file.', 'danger')

        except Exception as e:
            import traceback
            print("ERROR:", traceback.format_exc())
            flash(f'Server error: {e}', 'danger')

        return redirect(url_for('upload_data'))

    return render_template('upload.html', username=session['user_name'])

    
@app.route('/toggle_role/<int:user_id>', methods=['POST'])
def toggle_role(user_id):
    # Only allow admins
    if session.get('role') != 'admin':
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('users'))

    user = User.query.get_or_404(user_id)
    user.role = 'admin' if user.role == 'user' else 'user'
    db.session.commit()
    flash(f"Role for {user.username} changed to {user.role}.", 'success')
    return redirect(url_for('users'))

@app.route('/data')
def view_data():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    all_data = CallingData.query.all()
    return render_template('data.html', data=all_data, username=session['user_id'])

@app.route('/mark_called/<int:record_id>', methods=['POST'])
def mark_called(record_id):
    if 'user_id' not in session:
        flash('Login required.', 'danger')
        return redirect(url_for('login'))

    record = CallingData.query.get_or_404(record_id)
    record.remarks = request.form['remarks']
    record.called_by = session.get('user_name')
    record.status = 'called'

    db.session.commit()
    flash('Call marked successfully.', 'success')
    return redirect(url_for('view_data'))



if __name__ == '__main__':
    app.run(debug=True)