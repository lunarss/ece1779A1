from flask import render_template, session

from app import webapp

# webapp.secret_key = ajsdadbwa'xfadad\fea]'

@webapp.route('/index',methods=['GET'])
@webapp.route('/main',methods=['GET'])
def main():
    if 'username' in session:

        return render_template("main.html")

    return render_template("/login/login.html", error_msg = "Please sign in first.")