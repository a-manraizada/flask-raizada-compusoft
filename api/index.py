from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'super secret key'

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