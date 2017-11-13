from flask import Flask, redirect, render_template, session, request,flash
from mysqlconnection import MySQLConnector

app = Flask(__name__)
app.secret_key = 'SecretKeepItSafe'

mysql = MySQLConnector(app,'users_db')

@app.route('/')
def index():
    return redirect('/users')

@app.route('/users')
def users():
    query = "SELECT * from users"
    data ={}
    users =  mysql.query_db(query, data)
    return render_template('users.html', users = users)

@app.route('/users/<id>')
def getUser(id):
    query = "SELECT users.firstname, users.lastname, users.email,  DATE_FORMAT(users.created_at, '%M %D %Y') AS created_at from users WHERE users.id=:id"
    data = {
        'id' : id
    }
    result = mysql.query_db(query, data)
    if len(result) != 0:
        fname = result[0]['firstname']
        lname = result[0]['lastname']
        email = result[0]['email']
        created = result[0]['created_at']
        return render_template('show.html', id=id, fname=fname, lname=lname, email=email, created=created)
    else:
        flash("There is no user with id :"+id)
        return redirect('/')

@app.route('/users/new')
def new():
    return render_template('new.html')

@app.route('/create', methods=['POST'])
def create():    
    query = "INSERT into users(firstname, lastname, email, created_At, updated_at) VALUES(:firstname, :lastname, :email, NOW(), NOW());"
    data = {
        'firstname': request.form['fname'],
        'lastname': request.form['lname'],
        'email': request.form['email']
    }
    mysql.query_db(query, data)
    return redirect('/')

@app.route('/users/<id>/edit')
def edit(id):
    query = "SELECT * from users WHERE users.id=:id"
    data = {
        'id' : id
    }
    result = mysql.query_db(query, data)
    fname = result[0]['firstname']
    lname = result[0]['lastname']
    email = result[0]['email']
    return render_template('edit.html', id=id, fname=fname, lname=lname, email=email)

@app.route('/update', methods=['POST'])
def update():
    print request.form
    query = "UPDATE users SET firstname=:firstname, lastname=:lastname, email=:email, updated_at=NOW() WHERE id=:id"
    data ={
        'id' :request.form['userid'],
        'firstname':request.form['fname'],
        'lastname':request.form['lname'],
        'email':request.form['email']        
    } 
    result = mysql.query_db(query, data)
    print result
    return redirect('/')

@app.route('/<id>/delete', methods=['POST'])
def delete(id):
    query = "Delete FROM users WHERE users.id=:id"
    data={
        'id':id
    }
    mysql.query_db(query, data)
    return redirect('/')

app.run(debug='True')