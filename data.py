from flask_mysqldb import MySQL
import mysql.connector


mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="final_db"
)

cur = mydb.cursor()

def total_Vehicles():

    cur.execute("SELECT * FROM vehicles")
    rows = cur.fetchall()
    total = (len(rows))
    return total

def total_Allowed():

    cur.execute("SELECT * FROM vehicles WHERE status = 'allowed'")
    rows = cur.fetchall()
    total = (len(rows))
    return total

def total_NotAllowed():

    cur.execute("SELECT * FROM vehicles WHERE status = 'not allowed'")
    rows = cur.fetchall()
    total = (len(rows))
    return total



        

