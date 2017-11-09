from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app = Flask(__name__)
app.secret_key = 'SecretKeepItSafe'
mysql = MySQLConnector(app,'emails')
@app.route('/')
def index():
    query = "SELECT * FROM emails"                           # define your query
    emails = mysql.query_db(query)                           # run query with query_db()
    return render_template('index.html')                     # pass data to our template

@app.route('/save', methods=['POST'])
def add():
    email_input = request.form['email']
    isValid = True
    if EMAIL_REGEX.match(email_input):
        query = "SELECT * FROM emails"                           
        emails = mysql.query_db(query)
        if len(emails) == 0:
            query = "INSERT INTO emails(email , created_at) VALUES (:email, NOW() )"   
            data = {
                'email': request.form['email']    
                }
            mysql.query_db(query, data)
            return redirect('/success')
        else:
            for i in emails:
                if i['email'] == email_input:
                    isValid = False
                    flash("Email Address "+email_input+" is already exist, Please try another id")    
                    return redirect('/')
            if(isValid):
                query = "INSERT INTO emails(email , created_at) VALUES (:email, NOW() )"   
                data = {
                    'email': request.form['email']    
                    }
                mysql.query_db(query, data)
                flash("The email address you entered "+email_input +" is a VALID email address! Thank you!")
                return redirect('/success')
       
    else:
        flash("Invalid email address")
    return redirect('/')

@app.route('/success')
def emails():
    query = "SELECT * FROM emails"                           
    emails = mysql.query_db(query)
    return render_template('success.html',emails = emails)

@app.route('/delete', methods=['POST'])
def delete():
    print request.form
    emailId = request.form['email']
    query = "DELETE FROM emails WHERE email = :email"
    data = {"email" : emailId}
    mysql.query_db(query, data)
    flash("The email address "+emailId +" has been deleted successfully!")
    return redirect('/success')
app.run(debug=True)