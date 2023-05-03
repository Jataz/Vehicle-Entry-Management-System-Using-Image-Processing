from datetime import datetime
from flask import Flask, render_template, request, url_for, redirect,flash, session,jsonify, Response,g
from flask_mysqldb import MySQL
import mysql.connector
import MySQLdb.cursors
from werkzeug.security import generate_password_hash, check_password_hash 
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_ckeditor import CKEditor
import sqlite3
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None
    con = sqlite3.connect("vemuis.db")
    cur = con.cursor()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        con.close()

        if user and check_password_hash(user[5], password):
            session['loggedin'] = True
            session['userid'] = user[0]
            session['name'] = user[2]
            session['username'] = user[1]
            message = 'Logged in successfully!'
            return redirect(url_for('dashboard'))

        message = 'Please enter correct username / password!'
    return render_template('login.html', message=message)

    
@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

#Vehicle Routes
@app.route('/vehicles')
def vehicles():
    vehicles = Vehicles.query.all()
    return render_template("vehicles.html", vehicles=vehicles)

@app.route('/create_vehicle', methods = ["POST"])
def create_vehicle():
    con = sqlite3.connect('vemuis.db')
    cur = con.cursor()
    if request.method == "POST":

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
        cur.execute(" INSERT INTO vehicles (owner,id_number,phone_number,email,vehicle_name,model,number_plate,color,role,status) VALUES( ?,?,?,?,?,?,?,?,?,?)",(owner,id_number,phone_number,email,vehicle_name,model,number_plate,color,role,status))
        con.commit()
        flash("Vehilce Created Successfully")
        con.close()      
          
        return redirect(url_for('vehicles'))



@app.route('/update_vehicle', methods=['POST', 'GET'])
def update_vehicle():
    con = sqlite3.connect('vemuis.db', timeout=1)
    cur = con.cursor()

    if request.method == "POST":
        owner = request.form['owner']
        id_number = request.form['id_number']
        phone_number = request.form['phone_number']
        email = request.form['email']
        vehicle_name = request.form['vehicle_name']
        model = request.form['model']
        number_plate = request.form['number_plate']
        color = request.form['color']
        role = request.form['role']
        status = request.form['status']

        # Check if request.form contains all required fields and field names match those in the query
        if owner and id_number and phone_number and email and vehicle_name and model and number_plate and color and role and status:
            # Check if number_plate is being passed correctly, since it is used in the WHERE clause of the UPDATE query
            cur.execute("SELECT * FROM vehicles WHERE id=?", (id,))
            vehicle = cur.fetchone()
            if vehicle is not None:
                cur.execute("""UPDATE vehicles SET 
                                id = ?,
                                owner =?,
                                id_number=?,
                                phone_number=?,
                                email=?,
                                vehicle_name=?,
                                model=?,
                                color =?,
                                role =?,
                                status = ?
                                WHERE id=?""",
                            (id, owner, id_number, phone_number, email, vehicle_name, model, color, role, status, number_plate))
                con.commit()
                flash("Details Updated Successfully")
            else:
                flash("Vehicle not found")
        else:
            flash("Missing information")

        con.close()

        return redirect(url_for('vehicles'))
    
@app.route('/view_vehicle')
def view_vehicle():
    con = sqlite3.connect('vemuis.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM vehicles")
    vehicles= cur.fetchall()
    cur.close()
    return render_template("vehicles.html", vehicles=vehicles)


#User routes 
@app.route('/users')
def users():
    con = sqlite3.connect('vemuis.db')
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM users ")
    users = cur.fetchall()
    cur.close()
    return render_template("users.html", users=users)
    
@app.route('/create_user', methods=['POST'])
def create_user():
    con = sqlite3.connect("vemuis.db")
    cur = con.cursor()
    if request.method == "POST":
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
    
        if password != confirm_password:
            flash("Password Dont Match")
        

        cur.execute("INSERT INTO users (username,name,email, phone_number,password) VALUES (?, ?,?,?, ?)", (username,name,email,phone_number, generate_password_hash(password)))
        con.commit()
        flash("User Created Successfully")
        con.close()
        
        return redirect(url_for('users'))

@app.route('/update_user', methods=['GET', 'POST'])
def update_user():
    con = sqlite3.connect("vemuis.db")
    cur = con.cursor()
    if request.method == "POST":
        username = request.form['username']
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']
        
        if username and name and email and phone_number and password:
        
            cur.execute("""UPDATE users SET 
                        username=?, 
                        name=?,
                        email=?,
                        phone_number=?, 
                        password=?
                        WHERE userid=?""", 
                        (username, name, email, phone_number, generate_password_hash(password)))
            con.commit()
            flash("User Updated Successfully")
            con.close()
            return redirect(url_for('users'))

    
@app.route('/')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)

