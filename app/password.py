from flask import render_template, request, url_for, g, redirect, session
from passlib.hash import sha256_crypt
from threading import Thread
from app import webapp
from flask_mail import Message
from app.email import send_email

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


@webapp.route('/password/change', methods = ['GET', 'POST'])
def password_change():
    # auth check
    if 'role' in session and 'username' in session and 'user_id' in session:
        if request.method == "POST":
            user_id = session['user_id']
            old_password = request.form.get("old_password", "")
            new_password1 = request.form.get("new_password1", "")
            new_password2 = request.form.get("new_password2", "")
            # form format checking
            if old_password == "":
                error_msg = "Please enter your oringinal password!"
                return render_template("password/passwordchange.html", error_msg = error_msg,
                    old_password = old_password, new_password1 = new_password1, new_password2 = new_password2)
            elif new_password1 == "":
                error_msg = "Password can't be empty!"
                return render_template("password/passwordchange.html", error_msg = error_msg,
                    old_password = old_password, new_password1 = new_password1, new_password2 = new_password2)
            elif new_password2 == "":
                error_msg = "Please confirm your new password!"
                return render_template("password/passwordchange.html", error_msg = error_msg,
                    old_password = old_password, new_password1 = new_password1, new_password2 = new_password2)
            elif new_password1 != new_password2:
                error_msg = "The passwords you provide must be identical!"
                return render_template("password/passwordchange.html", error_msg = error_msg,
                    old_password = old_password, new_password1 = new_password1, new_password2 = new_password2)

            cnx = get_db()
            cursor = cnx.cursor()
            # check if the old password match the record
            query = "SELECT password FROM tbl_user_info WHERE user_id = %s"
            cursor.execute(query, (user_id,))

            row = cursor.fetchone()

            if (sha256_crypt.verify(old_password, row[0]) == False):
                error_msg = "The password you provide does not match our record!"
                return render_template("password/passwordchange.html", error_msg = error_msg,
                    old_password = old_password, new_password1 = new_password1, new_password2 = new_password2)
            else:
                # encrpt and update password
                password = sha256_crypt.hash(new_password1)
                query = "UPDATE tbl_user_info SET password = %s WHERE user_id = %s"
                cursor.execute(query, (password, user_id))
                cnx.commit()
                # give success message
                error_msg = "Your password has been updated."
                return render_template("/main.html", error_msg = error_msg)

        return render_template("/password/passwordchange.html")

    else:
        return render_template("/login/login.html", error_msg = "Please sign in first")

@webapp.route('/password/recovery', methods = ['GET', 'POST'])
def password_recovery():
    if request.method == "POST":
        email_address = request.form.get("email_address", "")
        # form format checking
        if email_address == "":
            error_msg = "Please enter your email address!"
            return render_template("password/passwordrecovery.html", error_msg = error_msg,
                email_address = email_address)
        elif not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$", email_address):
            error_msg = "Please enter a valid email address!"
            return render_template("password/passwordrecovery.html", error_msg = error_msg,
                email_address = email_address)

        cnx = get_db()
        cursor = cnx.cursor()
        # check if the email address is recorded
        query = "SELECT * FROM tbl_user_info WHERE user_email = %s"
        cursor.execute(query, (email_address,))

        row = cursor.fetchone()

        if not row:
            error_msg = "Sorry, the email address you provided does not match our record."
            return render_template("password/passwordrecovery.html", error_msg = error_msg,
                email_address = email_address)
        else:
            # send email with password change link to the user
            username = row[1]
            msg = Message(subject = 'Password Reset', sender = 'leo1779project@gmail.com', 
                          recipients = [email_address])
            # msg.body = "Thank you for registering, your default password has been set to 123456. Please use the link below to change your password: \n"
            # get a token for the reset link, valid for 10 minute
            token = jwt.encode({"reset_password": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=600)}, webapp.config.get("JWT_SECRET_KEY"), algorithm='HS256')
            # email display message
            display_msg = "We have received your password recovery request. Please use the link below to reset your password:"
            msg.html = render_template('/password/passwordreset.html', token = token, username = username, display_msg = display_msg)
            Thread(target = send_email, args = (webapp, msg)).start()

            error_msg = "An email that contains the link for your password recovery has been sent!"

            return render_template("password/passwordrecovery.html", error_msg = error_msg,
                email_address = email_address)
    return render_template("/password/passwordrecovery.html")

@webapp.route('/password/reset/<token>', methods = ['GET', 'POST'])
def password_reset(token):
    try:
        username = jwt.decode(token, webapp.config.get("JWT_SECRET_KEY"), algorithm='HS256')["reset_password"]
    except Exception as e:
        print(e)
        error_msg = "Unauthorized access."
        return render_template("/login/login.html", error_msg = error_msg)
    
    if not username:
        error_msg = "User info lost, please retry."
        return render_template("login/login.html", error_msg = error_msg)

    return render_template("/password/passwordresetverified.html", token = token)

@webapp.route('/password/reset/verified/<token>', methods = ['POST'])
def password_reset_verified(token):
    password1 = request.form.get("password1", "")
    password2 = request.form.get("password2", "")

    if password1 == "":
        error_msg = "Password can't be empty!"
        return render_template("/password/passwordresetverified.html", token = token,
                password1 = password1, password2 = password2, error_msg = error_msg)
    elif password2 =="":
        error_msg = "Please confirm your new password!"
        return render_template("/password/passwordresetverified.html", token = token,
                password1 = password1, password2 = password2, error_msg = error_msg)
    elif password1 != password2:
        error_msg = "The passwords you provide must be identical!"
        return render_template("/password/passwordresetverified.html", token = token,
                password1 = password1, password2 = password2, error_msg = error_msg)

    try:
        username = jwt.decode(token, webapp.config.get("JWT_SECRET_KEY"), algorithm='HS256')["reset_password"]
    except Exception as e:
        print(e)
        error_msg = "Unauthorized access."
        return render_template("/login/login.html", error_msg = error_msg)

    cnx = get_db()
    cursor = cnx.cursor()
    # encrpt and update password
    password = sha256_crypt.hash(password1)
    query = "UPDATE tbl_user_info SET password = %s WHERE user_name = %s"
    cursor.execute(query, (password, username))
    cnx.commit()
    # give success message
    error_msg = "Your password has been updated."
    return render_template("/login/login.html", error_msg = error_msg)