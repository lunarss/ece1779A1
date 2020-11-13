from flask import render_template, request, url_for, g, redirect, make_response, session
from passlib.hash import sha256_crypt
from app import webapp

import mysql.connector

from app.config import db_config


def connect_to_database():
    return mysql.connector.connect(user=db_config['user'], 
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'],
                                   autocommit=True)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db

@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@webapp.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == "":
            error_msg = "Please enter your username!"
            return render_template("login/login.html",error_msg=error_msg,
                username=username, password=password)
        elif password =="":
            error_msg = "Please enter your password!"
            return render_template("login/login.html",error_msg=error_msg,
                username=username, password=password)

    
        cnx = get_db()

        cursor = cnx.cursor()

        query = "SELECT password, user_role, user_id FROM tbl_user_info WHERE user_name = %s"
        cursor.execute(query, (username,))

        row = cursor.fetchone()

        if not row:
            error_msg = "User does not exist."
            return render_template("login/login.html", error_msg=error_msg,
                username=username, password=password)
        else:
            verified_password = row[0]

        if (sha256_crypt.verify(password, verified_password) == False):
            error_msg = "The password you provided was incorrect."
            return render_template("login/login.html", error_msg=error_msg,
                username=username, password=password)
        else:
            session['username'] = request.form["username"]
            session['role'] = row[1]
            session['user_id'] = row[2]
            resp = make_response(render_template("main.html"))
            return resp

    if 'username' in session:
        return render_template("main.html")
    
    return render_template("login/login.html")

@webapp.route('/logout')
def logout():
    session.pop('username', None)
    session.pop("role", None)
    return redirect(url_for("login"))