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
mysql = MySQLConnector(app,'wall')

@app.before_first_request
def setup():
     session['id'] = 0
     session['firstname'] =''

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup')
def signup():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    print request.form    
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
        session['firstname'] = fname
        session['id'] = mysql.query_db(query,data)  
        # flash("You have successfully registered !")
        return redirect('/wall')

@app.route('/loggedIn')
def loggedin():
    if 'id' in session:
        query = "SELECT * from users WHERE users.id=:id"
        data = {'id': session['id']}
        user = mysql.query_db(query, data)      
        fname = user[0]['firstname']
        lname = user[0]['lastname']
        emailId= user[0]['email']    
    return render_template('confirm.html', fname=fname, lname=lname, email=emailId)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['passwrd']
    query = "SELECT * from users WHERE users.email=:email"
    data = {'email': username}
    result = mysql.query_db(query,data)
    if len(result) >0 :
        dbPassword = md5.new(password + result[0]['salt']).hexdigest()
        if result[0]['password'] == dbPassword:
            session['id'] = result[0]['id']
            session['firstname'] =result[0]['firstname']
            return redirect('/wall')
    else:
        flash("Invalid username or password")
        return redirect('/')

@app.route('/post', methods=['POST'])
def post():
    message =  request.form['message']
    if len(message)>0:
        query = "INSERT INTO messages(message, created_at, updated_at, user_id) VALUES(:message, NOW(), NOW(), :user_id)"
        data = {
            'message' : request.form['message'],
            'user_id' : session['id']
        }
        mysql.query_db(query, data)       
    return redirect('/wall')

@app.route('/comment', methods=['POST'])
def comment():
    comment = request.form['comment']
    if len(comment)>0:
        query = "INSERT INTO comments(comment, created_at, updated_at, user_id, message_id) VALUES(:comment, NOW(), NOW(), :user_id, :message_id)"
        data = {
            'comment' : request.form['comment'],
            'user_id' : session['id'],
            'message_id':request.form['msgid']
        }
        mysql.query_db(query, data)    
    return redirect('/wall')

@app.route('/wall')
def wall():
    query = "SELECT users.id as user_id, users.firstname, users.lastname, messages.message, messages.id, DATE_FORMAT(messages.created_at, '%M %D %Y') AS created_at,TIME_TO_SEC(timediff( NOW(),           messages.created_at))/60 AS time_elapsed from users JOIN messages ON messages.user_id = users.id"
    messages = mysql.query_db(query)
    session['firstname']
    comment_query = "SELECT users.firstname, users.lastname, comments.comment, messages.id as msgId, comments.message_id AS cmsgId, DATE_FORMAT(comments.created_at, '%M %D %Y') AS created_at                     FROM users JOIN comments ON users.id = comments.user_id JOIN messages ON messages.id = comments.message_id"
    comments = mysql.query_db(comment_query)
   
    return render_template('wall.html', messages=messages, comments=comments)

@app.route('/delete', methods=['POST'])
def delete():       
    msg_id =  request.form['msg']  
    delete_comments = "DELETE FROM comments  WHERE comments.message_id = :message_id"
    data = {'message_id' : msg_id }
    mysql.query_db(delete_comments, data)

    delete_message = "DELETE FROM messages WHERE messages.id = :id"
    data = { 'id' : msg_id    }
    mysql.query_db(delete_message, data)
    
    return redirect('/wall')    

@app.route('/logoff')
def reset():
    return redirect('/')
app.run(debug='True')
