from flask import Flask, redirect, render_template, session, request,flash
import re
from datetime import datetime
from mysqlconnection import MySQLConnector
import os, binascii
import md5

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
NAME_REGEX = re.compile(r'^[a-zA-Z][\sa-zA-Z]*$') #https://stackoverflow.com/questions/290449/how-do-i-disallow-numbers-in-a-regular-expression
PWD_REGEX = re.compile(r'^(?=.*?[A-Z]).*\d') #https://stackoverflow.com/questions/33588441/python-regex-password-must-contain-at-least-one-uppercase-letter-and-number
app = Flask(__name__)
app.secret_key = 'SecretKeepItSafe'
mysql = MySQLConnector(app,'users')

@app.before_first_request
def setup():
     session['id'] = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register(): 
    error = False
    email_id = request.form['email']
    fname = request.form['fname']
    lname = request.form['lname']
    passwrd = request.form['password']
    confirm_pwd = request.form['confirm']
    bday = request.form['bday']
    if bday != "":
        bday = datetime.strptime(bday,"%Y-%m-%d")
    CurrentDate = datetime.now()
 
    query = " SELECT * FROM users WHERE users.email=:email"
    data = {
        'email':email_id
    }
    user = mysql.query_db(query, data)
    print user
    if user == None:
        if email_id == "" or fname =="" or lname=="" or passwrd =="" or confirm_pwd =="" or bday =="":
            error = True
            flash("All fields are required and must not be blank")
        else:
            if fname != "":
                if not NAME_REGEX.match(fname):
                    error = True
                    flash("Invalid first name ("+fname+") cannot have number ")
            if lname != "":
                if not NAME_REGEX.match(lname):
                    error = True
                    flash("Invalid last name ("+lname+") cannot have number ")
            if email_id != "":
                if not EMAIL_REGEX.match(email_id):
                    error = True
                    flash("Invalid Email Address! please follow abc@xyz.com")  
                
            if len(passwrd) < 8:
                error = True
                flash("Password should be more than 8 characters")
            elif not PWD_REGEX.match(passwrd):
                error = True
                flash("Invalid password! Password must contain atleast 1 Uppercase and 1 numeric value")    
            elif passwrd != confirm_pwd:
                error = True
                flash("Password and Password Confirmation are not matching")
            if bday > CurrentDate:
                error = True
                flash("Please enter valid date")
    
        if error:
            return redirect('/signup')
        else:
            password = passwrd
            salt =  binascii.b2a_hex(os.urandom(15))
            hashed_pw = md5.new(password + salt).hexdigest()
            query = "INSERT INTO users(firstname, lastname, email, birthdate, password, created_at, updated_at, salt) VALUES(:firstname, :lastname, :email, :birthdate, :password, NOW(), NOW(),:salt)"
            data = {
                'firstname': fname,
                'lastname': lname,
                'email': email_id,
                'birthdate': bday,
                'password':hashed_pw,
                'salt': salt
            }
            session['id'] = mysql.query_db(query,data)  
            flash("You have successfully registered !")
            return redirect('/loggedIn')
    else:
        flash("Please use another email id, this id is already in use")
        return redirect('/signup')

@app.route('/loggedIn')
def loggedin():
    # print session['id']
    if 'id' in session:
        query = "SELECT * from users WHERE users.id=:id"
        data = {'id': session['id']}
        user = mysql.query_db(query, data)
        print "user after register"
        fname = user[0]['firstname']
        lname = user[0]['lastname']
        emailId= user[0]['email']    
        return render_template('confirm.html', fname=fname, lname=lname, email=emailId)
    else:
        return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    validLogin = False
    username = request.form['username']
    password = request.form['passwrd']
    query = "SELECT * from users WHERE users.email=:email"
    data = {'email': username}
    result = mysql.query_db(query,data)
    dbPassword = md5.new(password + result[0]['salt']).hexdigest()
    if result[0]['password'] == dbPassword:
        # validLogin = True
        session['id'] = result[0]['id']
        flash("You have successfully logged in !")
        return redirect('/loggedIn')
    else:
        flash("Invalid username or password")
        return redirect('/')

@app.route('/reset')
def reset():
    session.clear()
    return redirect('/')
app.run(debug='True')
