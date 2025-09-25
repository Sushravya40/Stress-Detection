import pandas as pd 
import numpy as np 
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestRegressor, StackingRegressor
from sklearn.tree import ExtraTreeRegressor
from sklearn.ensemble import AdaBoostRegressor
from sklearn.metrics import mean_absolute_error,mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from flask import *
import mysql.connector
admin_email = "admin@example.com"
admin_password = "admin123"

#Connects to MySQL database Stress1.
db=mysql.connector.connect(host='localhost',user="root",password="",port='3306',database='Stress1')
cur=db.cursor()

#Initializes the Flask app with a secret key for managing sessions
app=Flask(__name__)
app.secret_key = "fghhdfgdfgrthrttgdfsadfsaffgd"

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/home')
def home():
    return render_template("userhome.html")


from flask import request, session, redirect, url_for, render_template, flash

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    msg = ''
    if request.method == 'POST':
        email = request.form['email']       # ✅ Use 'email' instead of 'username'
        password = request.form['password']

        # Dummy credentials for example
        if email == 'admin@example.com' and password == 'admin123':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_panel'))
        else:
            msg = 'Invalid email or password!'
    return render_template('admin_login.html', msg=msg)




from flask import session, redirect, url_for, flash, render_template

@app.route('/admin_panel')
def admin_panel():
    if not session.get('admin_logged_in'):
        flash('Please log in as admin to access the admin panel.', 'danger')
        return redirect(url_for('admin_login'))

    # Only run these if the admin is logged in
    cur.execute("SELECT * FROM allowed_emails")
    allowed_emails = cur.fetchall()

    cur.execute("SELECT Id, Name, Email FROM user")
    registered_users = cur.fetchall()

    return render_template('admin_panel.html',
                           allowed_emails=allowed_emails,
                           registered_users=registered_users)

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
        db.commit()
        flash("✅ Email added successfully", "success")
    except:
        db.rollback()
        flash("❌ Failed to add email", "danger")
    return redirect(url_for('admin_panel'))


@app.route('/admin/delete_email/<int:id>')
def delete_email(id):
    try:
        cur.execute("DELETE FROM allowed_emails WHERE id=%s", (id,))
        db.commit()
        flash("✅ Allowed email deleted successfully", "success")
    except:
        db.rollback()
        flash("❌ Failed to delete allowed email", "danger")
    return redirect(url_for('admin_panel'))


@app.route('/admin/delete_user/<int:id>')
def delete_user(id):
    try:
        cur.execute("DELETE FROM user WHERE Id=%s", (id,))
        db.commit()
        flash("✅ Registered user deleted successfully", "success")
    except:
        db.rollback()
        flash("❌ Failed to delete user", "danger")
    return redirect(url_for('admin_panel'))


#Displays login page and processes login POST requests.
@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=='POST':
        useremail=request.form['useremail']
        session['useremail']=useremail
        userpassword=request.form['userpassword']
        sql="select count(*) from user where Email='%s' and Password='%s'"%(useremail,userpassword)
        # cur.execute(sql)
        # data=cur.fetchall()
        # db.commit()

        #Verifies credentials from the database.
        x=pd.read_sql_query(sql,db)
        print(x)
        print('########################')
        count=x.values[0][0]

        from flask import flash, redirect, url_for
        if count == 0:
            flash("❌ Invalid email or password. Please try again.", "danger")
            return redirect(url_for('login'))

        else:
            # Extract user info & store in session
            s="select * from user where Email='%s' and Password='%s'"%(useremail,userpassword)
            z=pd.read_sql_query(s,db)
            session['email']=useremail
            pno=str(z.values[0][4])
            print(pno)
            name=str(z.values[0][1])
            print(name)
            session['pno']=pno
            session['name']=name
            return render_template("userhome.html",myname=name)
    return render_template('login.html')


@app.route('/registration', methods=["POST", "GET"])
def registration():

    # ✅ Allowed email domains for IT employees
    allowed_domains = ['@techcorp.com', '@itcompany.com', '@cybertech.org', '@datasci.in', '@qaeng.com']

    if request.method == 'POST':
        username = request.form['username']
        useremail = request.form['useremail'].lower()
        userpassword = request.form['userpassword']
        conpassword = request.form['conpassword']
        Age = request.form['Age']
        contact = request.form['contact']

        # ✅ Check if email ends with a valid IT domain
        if not any(useremail.endswith(domain) for domain in allowed_domains):
            flash("❌ Registration allowed only for IT employees with approved email domains.", "danger")
            return redirect("/registration")

        # ✅ Password match check
        if userpassword == conpassword:
            cur.execute("SELECT * FROM user WHERE Email=%s", (useremail,))
            data = cur.fetchall()
            db.commit()

            if data == []:
                sql = "INSERT INTO user(Name, Email, Password, Age, Mob) VALUES (%s, %s, %s, %s, %s)"
                val = (username, useremail, userpassword, Age, contact)
                cur.execute(sql, val)
                db.commit()
                flash("✅ Registered successfully", "success")
                return redirect("/login")
            else:
                flash("⚠️ User already registered. Try logging in.", "warning")
                return redirect("/registration")
        else:
            flash("⚠️ Passwords do not match.", "warning")
            return redirect("/registration")

    return render_template('registration.html')


#Loads CSV dataset and renders in HTML table using to_html().
@app.route('/viewdata',methods=["GET","POST"])
def viewdata():
    dataset = pd.read_csv(r'D:\C drive download\Downloads\TK191129--STRESS DETECTION IN IT PROFESSIONALS USING MACHINE LEARNING\CODE\FROUNTEND\stress_detection_IT_professionals_dataset.csv')
    dataset.to_html()
    print(dataset)
    print(dataset.head(2))
    print(dataset.columns)
    return render_template("viewdata.html", columns=dataset.columns.values, rows=dataset.values.tolist())
#Loads the CSV file and splits into x (features) and y (labels).

@app.route('/preprocess', methods=['GET'])
def preprocess():
    global x, y, x_train, x_test, y_train, y_test, df

    # Load and preprocess automatically
    df = pd.read_csv(r'D:\C drive download\Downloads\TK191129--STRESS DETECTION IN IT PROFESSIONALS USING MACHINE LEARNING\CODE\FROUNTEND\stress_detection_IT_professionals_dataset.csv')

    x = df.drop('Stress_Level', axis=1)
    y = df['Stress_Level']

    # Default test size = 30%
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=42)

    print("X_train shape:", x_train.shape)
    print("Y_train shape:", y_train.shape)
    print("X_test shape:", x_test.shape)
    print("Y_test shape:", y_test.shape)

    return render_template('preprocess.html', msg='✅ Data preprocessed automatically using 30% test split.')

#Chooses and trains models based on user selection (algo from form).
@app.route('/model', methods=["POST", "GET"])
def model():
    global x_train, y_train, x_test, y_test
    try:
        _ = x_train.shape  # Check if x_train is defined
    except NameError:
        return render_template("model.html", msg="⚠️ Please run Preprocess first!")

    if request.method == "POST":
        s = int(request.form['algo'])

        if s == 0:
            return render_template('model.html', msg="Choose an algorithm")

        elif s == 1:
            rf = RandomForestRegressor()
            rf.fit(x_train, y_train)
            y_pred = rf.predict(x_test)
            score = r2_score(y_pred, y_test) * 100
            return render_template("model.html", msg=f"RandomForestRegressor Accuracy: {score:.2f}%")

        elif s == 2:
            ad = AdaBoostRegressor()
            ad.fit(x_train, y_train)
            y_pred = ad.predict(x_test)
            score = r2_score(y_pred, y_test) * 100
            return render_template("model.html", msg=f"AdaBoostRegressor Accuracy: {score:.2f}%")

        elif s == 3:
            ex = ExtraTreeRegressor()
            ex.fit(x_train, y_train)
            y_pred = ex.predict(x_test)
            score = r2_score(y_pred, y_test) * 100
            return render_template("model.html", msg=f"ExtraTreeRegressor Accuracy: {score:.2f}%")

        elif s == 4:
            base_model = [
                ('rf', RandomForestRegressor()),
                ('dt', ExtraTreeRegressor()),
            ]
            meta_model = AdaBoostRegressor()
            stc = StackingRegressor(estimators=base_model, final_estimator=meta_model)
            stc.fit(x_train, y_train)
            y_pred = stc.predict(x_test)
            score = r2_score(y_pred, y_test) * 100
            return render_template("model.html", msg=f"Stacking Accuracy: {score:.2f}%")

        elif s == 5:
            from sklearn.tree import DecisionTreeClassifier
            dt = DecisionTreeClassifier()
            dt.fit(x_train, y_train)
            y_pred = dt.predict(x_test)
            score = r2_score(y_pred, y_test) * 100
            return render_template("model.html", msg=f"DecisionTree Accuracy: {score:.2f}%")

    return render_template("model.html")


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
            print(lee)

            # 🚫 Invalid input checks
            if all(v == 0 for v in lee) or any(v < 0 for v in lee):
                msg = "⚠️ Invalid input: All fields must be filled with non-zero, non-negative values."
                return render_template("prediction.html", msg=msg)

            if f1 > 200 or f2 > 20 or f3 > 24 or f4 > 500 or f5 > 15:
                msg = "⚠️ One or more fields exceed realistic human/workplace limits. Please enter valid values."
                return render_template("prediction.html", msg=msg)

        except (ValueError, KeyError):
            msg = "⚠️ Invalid input: Please make sure all fields are filled with valid numbers."
            return render_template("prediction.html", msg=msg)

        # ✅ Train model and predict
        model = RandomForestRegressor()
        model.fit(x_train, y_train)
        result = model.predict([lee])
        print(result)

        # 💾 Save result to database
        sql = """
        INSERT INTO stress_prediction 
        (email, heart_rate, skin_conductivity, hours_worked, emails_sent, meetings_attended, prediction, date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        val = (email, f1, f2, f3, f4, f5, float(result[0]), date)
        cur.execute(sql, val)
        db.commit()

        # 🧠 Result Message and Suggestions
        stress_value = float(result[0])
        msg = f"The Stress level of this IT Professional is {stress_value:.2f}%"
        counseling_links = None

        if stress_value < 20:
            suggestion = """Low Stress: Great job! Maintain your routine with
                            - Regular physical activity
                            - Adequate sleep
                            - Balanced diet"""
        elif stress_value < 30:
            suggestion = """Moderate Stress: Consider:
                            - Taking short breaks between tasks
                            - Practicing deep breathing or meditation
                            - Avoiding multitasking"""
        else:
            suggestion = """High Stress: Immediate attention recommended:
                            - Speak to a counselor or mental health expert
                            - Reduce screen time & emails after work hours
                            - Take a few days off to rest and recover"""
            counseling_links = [
                {"name": "NIMHANS", "url": "https://www.nimhans.ac.in/"},
                {"name": "iCall by TISS", "url": "https://icallhelpline.org/"},
                {"name": "YourDOST", "url": "https://yourdost.com/"},
                {"name": "BetterLYF", "url": "https://www.betterlyf.com/"},
                {"name": "MindPeers", "url": "https://www.mindpeers.co/"},
            ]

        return render_template('prediction.html', msg=msg, suggestion=suggestion, counseling_links=counseling_links)

    return render_template("prediction.html")


from datetime import datetime, timedelta

@app.route('/dashboard')
def dashboard():
    email = session.get('email')
    filter_type = request.args.get('filter', 'all')  # default = 'all'

    if filter_type == 'week':
        from datetime import datetime, timedelta
        today = datetime.today()
        week_ago = today - timedelta(days=7)
        cur.execute("""
            SELECT date, prediction FROM stress_prediction 
            WHERE email = %s AND date >= %s 
            ORDER BY date
        """, (email, week_ago.strftime('%Y-%m-%d')))
    else:
        cur.execute("""
            SELECT date, prediction FROM stress_prediction 
            WHERE email = %s 
            ORDER BY date
        """, (email,))

    data = cur.fetchall()
    dates = [str(row[0]) for row in data]
    stress_levels = [row[1] for row in data]

    return render_template('dashboard.html', dates=dates, stress_levels=stress_levels, current_filter=filter_type)

#Starts the Flask app in debug mode.
if __name__=="__main__":
    app.run(debug=True)