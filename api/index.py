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
class UserData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    age = db.Column(db.Integer)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Initialize DB
with app.app_context():
    db.create_all()

@app.route('/home')
def home():
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

    return f"Welcome, {session['user_name']}!"

@app.route('/about')
def about():
    return 'About'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('User already exists.', 'warning')
            return redirect(url_for('register'))

        new_user = User(name=name, email=email)
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
            session['user_name'] = user.name
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

import traceback

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(url_for('home'))

        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'warning')
            return redirect(url_for('home'))

        if file and file.filename.endswith('.xlsx'):
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            df = pd.read_excel(filepath)
            for _, row in df.iterrows():
                user = UserData(name=row['Name'], email=row['Email'], age=int(row['Age']))
                db.session.add(user)
            db.session.commit()
            flash('Data uploaded successfully!', 'success')

        else:
            flash('Invalid file type. Please upload a .xlsx file.', 'danger')
        return redirect(url_for('home'))

    except Exception as e:
        print("ERROR:", traceback.format_exc())  # Vercel logs
        flash(f'Server error: {e}', 'danger')
        return redirect(url_for('home'))

@app.route('/data')
def view_data():
    if 'username' not in session:
        return redirect(url_for('login'))

    all_data = UserData.query.all()
    return render_template('data.html', data=all_data, username=session['username'])