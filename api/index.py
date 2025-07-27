from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import os

# app = Flask(__name__)
app = Flask(__name__, instance_path='/tmp/flask_instance')
app.secret_key = 'super secret key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)


# Create a simple model
class UserData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    age = db.Column(db.Integer)

# Initialize DB
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    return 'Hello, World! <a href="/login">Login</a>'

@app.route('/about')
def about():
    return 'About'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == 'password':
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return 'Invalid credentials. <a href="/login">Try again</a>'

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
