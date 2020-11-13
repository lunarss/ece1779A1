from flask import render_template, request, url_for, g, redirect, session, jsonify
from passlib.hash import sha256_crypt
from threading import Thread
from flask_mail import Message
from app.email import send_email
from app import webapp

import datetime
import jwt
import re
import mysql.connector

from app.config import db_config

error_msg = None

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

@webapp.route('/user/list', methods = ['GET'])
def user_list():
    # auth check
    if 'role' in session and 'username' in session and 'user_id' in session:
        if session['role'] != 1:
            error_msg = "You have to be a privileged user to be able to use this feature."
            return render_template("main.html", error_msg = error_msg)

        cnx = get_db()

        cursor = cnx.cursor()

        query = "SELECT user_id, user_name, user_email FROM tbl_user_info WHERE user_role = 0"

        cursor.execute(query)
    
        return render_template("user/userlist.html", title = "User Management", cursor = cursor)
    
    else:
        return render_template("/login/login.html", error_msg = "Please sign in first")

@webapp.route('/user/create', methods = ['GET', 'POST'])
def user_create():
    # auth check
    if 'role' in session and 'username' in session and 'user_id' in session:
        if session['role'] != 1:
            error_msg = "You have to be a privileged user to be able to use this feature."
            return render_template("main.html", error_msg = error_msg)
        
        # code to execute if it is a post request
        if request.method == "POST":
            username = request.form.get("username", "")
            email_address = request.form.get("email_address", "")

            # form format checking
            if username == "":
                error_msg = "You must put in a username!"
                return render_template("user/usercreate.html",title="Create User Account",
                    error_msg=error_msg, username=username, email_address=email_address)
            elif email_address =="":
                error_msg = "You must put in an email address!"
                return render_template("user/usercreate.html",title="Create User Account",
                    error_msg=error_msg, username=username, email_address=email_address)
            elif not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", email_address):
                error_msg = "Please enter a valid email address!"
                return render_template("user/usercreate.html",title="Create User Account",
                    error_msg=error_msg, username=username, email_address=email_address)

            default_password = sha256_crypt.hash("123456")
            cnx = get_db()
            cursor = cnx.cursor()
            # check if the username is used
            query = "SELECT * FROM tbl_user_info WHERE user_name = %s"
            cursor.execute(query, (username,))

            row = cursor.fetchone()

            if row:
                error_msg = "User name already in use!"
                return render_template("user/usercreate.html",title="Create User Account",
                    error_msg=error_msg, username=username, email_address=email_address)
            else:
                # check if the email address is used
                query = "SELECT * FROM tbl_user_info WHERE user_email = %s"
                cursor.execute(query, (email_address,))

                row = cursor.fetchone()
                
                if row:
                    error_msg = "This email address has been used."
                    return render_template("user/usercreate.html",title="Create User Account",
                        error_msg=error_msg, username=username, email_address=email_address)

                # add user
                query = '''INSERT INTO tbl_user_info(user_name, password, user_email) 
                            VALUES(%s, %s, %s)'''
            
    
                cursor.execute(query,(username,default_password,email_address))
                cnx.commit()

                # send email with password change link to the user
                msg = Message(subject = 'Registeration Confirmed', sender = 'leo1779project@gmail.com', 
                              recipients = [email_address])
                # msg.body = "Thank you for registering, your default password has been set to 123456. Please use the link below to change your password: \n"
                # get a token for the reset link, valid for 10 minutes
                token = jwt.encode({"reset_password": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=600)}, webapp.config.get("JWT_SECRET_KEY"), algorithm='HS256')
                # email display message
                display_msg = "Thank you for registering, your default password has been set to 123456. Please use the link below to change your password:"
                msg.html = render_template('/password/passwordreset.html', token = token, username = username, display_msg = display_msg)
                Thread(target = send_email, args = (webapp, msg)).start()
                # give success message
                error_msg = "User creation success, an email notification has been sent!"
                return render_template("user/usercreate.html",title="Create User Account",
                        error_msg=error_msg, username=username, email_address=email_address)

        # Code to execute if it is a get request
        return render_template("/user/usercreate.html", title = "Create User Account")

    
    else:
        return render_template("/login/login.html", error_msg = "Please sign in first")

@webapp.route('/user/delete/<int:id>', methods = ['POST'])
def user_delete(id):
    # auth check
    if 'role' in session and 'username' in session and 'user_id' in session:
        if session['role'] != 1:
            error_msg = "You have to be a privileged user to be able to use this feature."
            return render_template("main.html", error_msg = error_msg)

        # form format checking
        if not id:
            error_msg = "User information error, Please retry."
            return render_template("main.html", error_msg = error_msg)

        else:
            cnx = get_db()
            cursor = cnx.cursor()

            query = "DELETE FROM tbl_user_info WHERE user_id = %s"
            
            cursor.execute(query,(id,))
            cnx.commit()

            # give success message and reload with new list
            query = "SELECT user_id, user_name, user_email FROM tbl_user_info WHERE user_role = 0"

            cursor.execute(query)
            
            error_msg = "User delete success!"
            return render_template("user/userlist.html", title = "User Management", cursor = cursor, error_msg = error_msg)

        return render_template("/user/usercreate.html", title = "Create User Account")

    # Code to execute if it is a get request
    else:
        return render_template("/login/login.html", error_msg = "Please sign in first")


@webapp.route('/api/register', methods = ['POST'])
def user_create_api():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # form format checking
    if username == "":
        error_msg = "You must put in a username!"
        rsp = {"success": "false", 
               "error": {
                   "code": 400,
                   "message": error_msg
               }}
        return jsonify(rsp), 400
    elif password =="":
        error_msg = "You must put in an email address!"
        rsp = {"success":"false", 
               "error": {
                   "code": 400,
                   "message": error_msg
               }}
        return jsonify(rsp), 400

    encrypted_password = sha256_crypt.hash(password)
    cnx = get_db()
    cursor = cnx.cursor()
    # check if the username is used
    query = "SELECT * FROM tbl_user_info WHERE user_name = %s"
    cursor.execute(query, (username,))

    row = cursor.fetchone()

    if row:
        error_msg = "User name already in use!"
        rsp = {"success": "false", 
               "error": {
                   "code": 409,
                   "message": error_msg
               }}
        return jsonify(rsp), 409
    else:
        # add user
        query = '''INSERT INTO tbl_user_info(user_name, password) 
                    VALUES(%s, %s)'''
            
    
        cursor.execute(query,(username,encrypted_password))
        cnx.commit()

        # return success
        rsp = {"success": "true"}
        return jsonify(rsp), 201

