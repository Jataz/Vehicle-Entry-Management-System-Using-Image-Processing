from datetime import datetime
from flask import Flask, render_template, request, url_for, redirect,flash, session,jsonify, Response,g
from flask_mysqldb import MySQL
import mysql.connector
import MySQLdb.cursors
from werkzeug.security import generate_password_hash, check_password_hash 
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_ckeditor import CKEditor

from flask_sqlalchemy import SQLAlchemy
import data as dt


app = Flask(__name__)
app.secret_key = "this-is-a-secret-key"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'anpr' 

mysql = MySQL(app)

#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/anpr'
# Secret Key!
# Initialize The Database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'static/images/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

td = dt.total_Vehicles()
tt = dt.total_Allowed()
tc = dt.total_NotAllowed()


class Vehicles(db.Model, UserMixin):
	vehicle_id = db.Column(db.Integer, primary_key=True)
	owner = db.Column(db.String(20), nullable=False, unique=True)
	model = db.Column(db.String(200), nullable=False)
	phone_number = db.Column(db.String(120), nullable=False, unique=True)
	color = db.Column(db.String(120))
	role = db.Column(db.Text(), nullable=True)
	status = db.Column(db.Text(), nullable=True)
	number_plate= db.Column(db.String(), nullable=True)
 

@app.route('/is_registered', methods=['POST', 'GET'])
def is_registered():
    
    plate = request.args.get('number_plate')
    
    vehicle = Vehicles.query.filter_by(number_plate=plate, status= 'allowed').first()
    
    is_registered = False
    
    if vehicle:
        is_registered = True
        
    response = jsonify({'registered': is_registered})
    
    response.headers.add('Content-Type', 'application/json')
    
    return response

@app.route('/', methods=['GET', 'POST'])
def home():
    
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['password'], password):
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['name'] = user['name']
            session['username'] = user['username']
            message = 'Logged in successfully!'
            #login_user(user)
            return redirect(url_for('dashboard'))

        message = 'Please enter correct username / password!'
    return render_template('login.html', message=message)

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html",td=td,tt=tt,tc=tc)

#Vehicle Routes
@app.route('/vehicles')
def vehicles():
    cur = mysql.connect.cursor()
    cur.execute("SELECT * FROM vehicles")
    vehicles = cur.fetchall()
    
    cur.close()
    return render_template("vehicles.html", vehicles=vehicles)

@app.route('/create_vehicle', methods = ["POST"])
def create_vehicle():
    if request.method == "POST":
        flash("Vehilce Created Successfully")
        owner = request.form['owner']
        id_number  = request.form['id_number']
        phone_number = request.form['phone_number']
        email = request.form['email']
        vehicle_name = request.form['vehicle_name']
        model = request.form['model']
        number_plate = request.form['number_plate']
        color = request.form['color']
        role = request.form['role']
        status = request.form['status']
        cur = mysql.connection.cursor()
        cur.execute(" INSERT INTO vehicles (owner,id_number,phone_number,email,vehicle_name,model,number_plate,color,role,status) VALUES( %s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(owner,id_number,phone_number,email,vehicle_name,model,number_plate,color,role,status))
        mysql.connection.commit()
        
        return redirect(url_for('vehicles'))
    

@app.route('/update_vehicle', methods=['POST'])
def update_vehicle():
    cur = mysql.connection.cursor()

    if request.method == "POST":
        vehicle_name = request.form['vehicle_name']
        model = request.form['model']
        number_plate = request.form['number_plate']
        color = request.form['color']
        status = request.form['status']

        # Check if request.form contains all required fields and field names match those in the query
        if vehicle_name and model and number_plate and color and status:
            # Check if number_plate is being passed correctly, since it is used in the WHERE clause of the UPDATE query
            cur.execute("SELECT * FROM vehicles WHERE number_plate=%s", (number_plate,))
            vehicle = cur.fetchone()
            if vehicle is not None:
                cur.execute("""UPDATE vehicles SET 
                                vehicle_name=%s,
                                model=%s,
                                color=%s,
                                status=%s
                                WHERE number_plate=%s""",
                            (vehicle_name, model, color, status, number_plate))
                mysql.connection.commit()
                flash("Status Updated Successfully")
            else:
                flash("Vehicle not found")
        else:
            flash("Missing information")
            
        return redirect(url_for('vehicles'))
    

#User routes 
@app.route('/users')
def users():
    
    cur = mysql.connect.cursor()
    cur.execute("SELECT * FROM users ")
    users = cur.fetchall()
    cur.close()
    return render_template("users.html", users=users)
    
@app.route('/create_user', methods=['POST'])
def create_user():
    if request.method == "POST":
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
    
        if password != confirm_password:
            error = 'Password does not Match'
            return render_template('ex_404.html', error=error)
        
        cur = mysql.connection.cursor()
        
        # Check if email already exists in the database
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if user:
            error = 'Email already exists'
            return render_template('ex_404.html', error=error)
        
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        username = cur.fetchone()
        if username:
            error = 'Username already exists'
            return render_template('ex_404.html', error=error)
        
        # If email doesn't exist, create the user
        cur.execute("INSERT INTO users (username,name,email, phone_number,password) VALUES (%s, %s,%s,%s, %s)", (username,name,email,phone_number, generate_password_hash(password)))
        mysql.connection.commit()
        
        return redirect(url_for('users'))
    

@app.route('/update_user', methods=['GET', 'POST'])
def update_user():
    cur = mysql.connection.cursor()
    if request.method == "POST":
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        
        if username and name and email and phone_number:
        
            cur.execute("""UPDATE users SET 
                        username=?, 
                        name=?,
                        email=?,
                        phone_number=?
                        WHERE email=?""", 
                        (username, name, email, phone_number))
            mysql.connection.commit()
            flash("User Updated Successfully")
            return redirect(url_for('users'))


@app.route('/')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)

