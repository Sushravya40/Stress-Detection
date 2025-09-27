import os
from flask import Flask, render_template, request, session, redirect, url_for, flash
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, StackingRegressor, AdaBoostRegressor
from sklearn.tree import ExtraTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

# -------------------------------
# DATABASE SETUP (PostgreSQL)
# -------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL") or "postgresql://stressdb_y8l1_user:nkUESsYvS6ESRcUCquMOTazBZjCa6GQ4@dpg-d3ae75fdiees73d6lkhg-a/stressdb_y8l1"
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor(cursor_factory=RealDictCursor)

# -------------------------------
# FLASK APP SETUP
# -------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# -------------------------------
# ADMIN CREDENTIALS
# -------------------------------
admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")

# -------------------------------
# GLOBAL VARIABLES FOR MODEL
# -------------------------------
x_train = x_test = y_train = y_test = df = None

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
        cur.execute("INSERT INTO allowed_emails (email) VALUES (%s)", (email,))
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
    if request.method=='POST':
        useremail = request.form['useremail']
        userpassword = request.form['userpassword']
        cur.execute("SELECT * FROM users WHERE Email=%s AND Password=%s", (useremail, userpassword))
        data = cur.fetchone()
        if not data:
            flash("❌ Invalid email or password. Please try again.", "danger")
            return redirect(url_for('login'))
        else:
            session['email'] = data['Email']
            session['name'] = data['Name']
            session['pno'] = str(data['Mob'])
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

        # Check email domain
        if not any(useremail.endswith(domain) for domain in allowed_domains):
            flash("❌ Registration allowed only for IT employees with approved email domains.", "danger")
            return redirect("/registration")

        # Password match
        if userpassword != conpassword:
            flash("⚠️ Passwords do not match.", "warning")
            return redirect("/registration")

        # Admin approval check
        cur.execute("SELECT * FROM allowed_emails WHERE email=%s", (useremail,))
        allowed = cur.fetchone()
        if not allowed:
            flash("⚠️ Your email is not approved by admin.", "danger")
            return redirect("/registration")

        # Existing user check
        cur.execute("SELECT * FROM users WHERE Email=%s", (useremail,))
        existing = cur.fetchone()
        if not existing:
            try:
                cur.execute("INSERT INTO users(Name, Email, Password, Age, Mob) VALUES (%s,%s,%s,%s,%s)",
                            (username, useremail, userpassword, Age, contact))
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
# DATASET LOAD & PREPROCESS
# -------------------------------
DATASET_URL = "https://YOUR_RENDER_FILE_URL/stress_detection_IT_professionals_dataset.csv"
x_train = x_test = y_train = y_test = df = None

@app.route('/viewdata', methods=["GET","POST"])
def viewdata():
    df = pd.read_csv(DATASET_URL)
    return render_template("viewdata.html", columns=df.columns.values, rows=df.values.tolist())

@app.route('/preprocess', methods=['GET'])
def preprocess():
    global x, y, x_train, x_test, y_train, y_test, df
    df = pd.read_csv(DATASET_URL)
    x = df.drop('Stress_Level', axis=1)
    y = df['Stress_Level']
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=42)
    return render_template('preprocess.html', msg='✅ Data preprocessed successfully!')

# -------------------------------
# MODEL TRAINING
# -------------------------------
@app.route('/model', methods=["POST", "GET"])
def model():
    global x_train, y_train, x_test, y_test
    try:
        _ = x_train.shape
    except NameError:
        return render_template("model.html", msg="⚠️ Please run Preprocess first!")

    if request.method == "POST":
        s = int(request.form['algo'])
        if s == 1:
            rf = RandomForestRegressor()
            rf.fit(x_train, y_train)
            y_pred = rf.predict(x_test)
            score = r2_score(y_test, y_pred) * 100
            return render_template("model.html", msg=f"RandomForestRegressor Accuracy: {score:.2f}%")
        elif s == 2:
            ad = AdaBoostRegressor()
            ad.fit(x_train, y_train)
            y_pred = ad.predict(x_test)
            score = r2_score(y_test, y_pred) * 100
            return render_template("model.html", msg=f"AdaBoostRegressor Accuracy: {score:.2f}%")
        elif s == 3:
            ex = ExtraTreeRegressor()
            ex.fit(x_train, y_train)
            y_pred = ex.predict(x_test)
            score = r2_score(y_test, y_pred) * 100
            return render_template("model.html", msg=f"ExtraTreeRegressor Accuracy: {score:.2f}%")
        elif s == 4:
            base_model = [('rf', RandomForestRegressor()), ('dt', ExtraTreeRegressor())]
            meta_model = AdaBoostRegressor()
            stc = StackingRegressor(estimators=base_model, final_estimator=meta_model)
            stc.fit(x_train, y_train)
            y_pred = stc.predict(x_test)
            score = r2_score(y_test, y_pred) * 100
            return render_template("model.html", msg=f"Stacking Accuracy: {score:.2f}%")
    return render_template("model.html")

# -------------------------------
# PREDICTION
# -------------------------------
@app.route('/prediction', methods=["POST", "GET"])
def prediction():
    if request.method == "POST":
        try:
            f1 = float(request.form['Heart_Rate'])
            f2 = float(request.form['Skin_Conductivity'])
            f3 = float(request.form['Hours_Worked'])
            f4 = float(request.form['Emails_Sent'])
            f5 = float(request.form['Meetings_Attended'])
            date = request.form['date']
            email = session.get('email')
            lee = [f1, f2, f3, f4, f5]
        except (ValueError, KeyError):
            msg = "⚠️ Invalid input. Fill all fields correctly."
            return render_template("prediction.html", msg=msg)

        model = RandomForestRegressor()
        model.fit(x_train, y_train)
        result = model.predict([lee])[0]

        cur.execute("""INSERT INTO stress_prediction 
                       (email, heart_rate, skin_conductivity, hours_worked, emails_sent, meetings_attended, prediction, date)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (email, f1, f2, f3, f4, f5, float(result), date))
        conn.commit()

        stress_value = float(result)
        if stress_value < 20:
            suggestion = "Low Stress: Maintain healthy routine, sleep well, exercise."
            counseling_links = None
        elif stress_value < 30:
            suggestion = "Moderate Stress: Take breaks, practice meditation, avoid multitasking."
            counseling_links = None
        else:
            suggestion = "High Stress: Seek counseling, reduce workload, rest."
            counseling_links = [
                {"name": "NIMHANS", "url": "https://www.nimhans.ac.in/"},
                {"name": "iCall by TISS", "url": "https://icallhelpline.org/"},
                {"name": "YourDOST", "url": "https://yourdost.com/"},
            ]
        msg = f"The Stress level of this IT Professional is {stress_value:.2f}%"
        return render_template('prediction.html', msg=msg, suggestion=suggestion, counseling_links=counseling_links)
    return render_template("prediction.html")

# -------------------------------
# DASHBOARD
# -------------------------------
@app.route('/dashboard')
def dashboard():
    email = session.get('email')
    filter_type = request.args.get('filter', 'all')
    if filter_type == 'week':
        today = datetime.today()
        week_ago = today - timedelta(days=7)
        cur.execute("""SELECT date, prediction FROM stress_prediction 
                       WHERE email=%s AND date >= %s ORDER BY date""", (email, week_ago.strftime('%Y-%m-%d')))
    else:
        cur.execute("""SELECT date, prediction FROM stress_prediction 
                       WHERE email=%s ORDER BY date""", (email,))
    data = cur.fetchall()
    dates = [str(row['date']) for row in data]
    stress_levels = [row['prediction'] for row in data]
    return render_template('dashboard.html', dates=dates, stress_levels=stress_levels, current_filter=filter_type)

# -------------------------------
# RUN APP
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
