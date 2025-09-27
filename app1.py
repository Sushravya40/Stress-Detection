import os
from flask import Flask, render_template, request, session, redirect, url_for, flash
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, StackingRegressor, AdaBoostRegressor
from sklearn.tree import ExtraTreeRegressor
from sklearn.metrics import r2_score
import psycopg2

# -------------------------------
# DATABASE SETUP (PostgreSQL)
# -------------------------------
DATABASE_URL = "postgresql://postgres:NewStrongPassword123!@localhost:5432/Stress1"
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()

# -------------------------------
# FLASK APP SETUP
# -------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# -------------------------------
# ADMIN CREDENTIALS
# -------------------------------
admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

# -------------------------------
# ROUTES
# -------------------------------
@app.route('/')
def index():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/home')
def home():
    return render_template("userhome.html")

# -------------------------------
# ADMIN LOGIN & PANEL
# -------------------------------
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    msg = ''
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == admin_email and password == admin_password:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            msg = 'Invalid email or password!'
    return render_template('admin_login.html', msg=msg)

@app.route('/admin_panel')
def admin_panel():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to access the admin panel.', 'danger')
        return redirect(url_for('admin_login'))

    try:
        cur.execute("SELECT * FROM allowed_emails")
        allowed_emails = cur.fetchall()

        cur.execute("SELECT Id, Name, Email FROM users")
        registered_users = cur.fetchall()
    except Exception as e:
        print(e)
        allowed_emails = []
        registered_users = []

    return render_template('admin_panel.html', allowed_emails=allowed_emails, registered_users=registered_users)

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash("🚪 Logged out successfully.", "info")
    return redirect(url_for('admin_login'))

@app.route('/admin/add_email', methods=['POST'])
def add_email():
    email = request.form['email']
    try:
        cur.execute("INSERT INTO allowed_emails (email) VALUES (%s) ON CONFLICT (email) DO NOTHING", (email,))
        conn.commit()
        flash("✅ Email added successfully", "success")
    except Exception as e:
        conn.rollback()
        flash(f"❌ Failed to add email: {str(e)}", "danger")
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_email/<int:id>')
def delete_email(id):
    try:
        cur.execute("DELETE FROM allowed_emails WHERE id=%s", (id,))
        conn.commit()
        flash("✅ Allowed email deleted successfully", "success")
    except:
        conn.rollback()
        flash("❌ Failed to delete allowed email", "danger")
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user/<int:id>')
def delete_user(id):
    try:
        cur.execute("DELETE FROM users WHERE Id=%s", (id,))
        conn.commit()
        flash("✅ Registered user deleted successfully", "success")
    except:
        conn.rollback()
        flash("❌ Failed to delete user", "danger")
    return redirect(url_for('admin_panel'))

# -------------------------------
# USER LOGIN & REGISTRATION
# -------------------------------
@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'POST':
        useremail = request.form['useremail']
        userpassword = request.form['userpassword']

        cur.execute("SELECT * FROM users WHERE Email=%s AND Password=%s", (useremail, userpassword))
        data = cur.fetchall()

        if not data:
            flash("❌ Invalid email or password. Please try again.", "danger")
            return redirect(url_for('login'))
        else:
            session['email'] = useremail
            session['name'] = data[0][1]
            session['pno'] = str(data[0][5])
            return render_template("userhome.html", myname=session['name'])
    return render_template('login.html')

@app.route('/registration', methods=["POST", "GET"])
def registration():
    allowed_domains = ['@techcorp.com', '@itcompany.com', '@cybertech.org', '@datasci.in', '@qaeng.com']

    if request.method == 'POST':
        username = request.form['username']
        useremail = request.form['useremail'].lower()
        userpassword = request.form['userpassword']
        conpassword = request.form['conpassword']
        Age = request.form['Age']
        contact = request.form['contact']

        if not any(useremail.endswith(domain) for domain in allowed_domains):
            flash("❌ Registration allowed only for IT employees with approved email domains.", "danger")
            return redirect("/registration")

        if userpassword != conpassword:
            flash("⚠️ Passwords do not match.", "warning")
            return redirect("/registration")

        cur.execute("SELECT * FROM users WHERE Email=%s", (useremail,))
        data = cur.fetchall()

        if not data:
            try:
                cur.execute(
                    "INSERT INTO users(Name, Email, Password, Age, Mob) VALUES (%s, %s, %s, %s, %s)",
                    (username, useremail, userpassword, Age, contact)
                )
                conn.commit()
                flash("✅ Registered successfully", "success")
                return redirect("/login")
            except Exception as e:
                conn.rollback()
                flash(f"❌ Registration failed: {str(e)}", "danger")
                return redirect("/registration")
        else:
            flash("⚠️ User already registered. Try logging in.", "warning")
            return redirect("/registration")

    return render_template('registration.html')

# -------------------------------
# RUN APP
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
