from flask_mail import Mail
from app import webapp


mail = Mail(webapp)

def send_email(app, msg):
    with app.app_context():
        mail.send(msg)