from flask import render_template, redirect, g, url_for, request, session, jsonify
from app import webapp
from passlib.hash import sha256_crypt
from werkzeug.utils import secure_filename

from datetime import datetime
import ssl
import requests
import time
import tempfile
import os
import mimetypes
import urllib.request as urllib2

import mysql.connector

from app.config import db_config

def connect_to_database():
    return mysql.connector.connect(user=db_config['user'], 
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'],
                                   autocommit=True)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db

@webapp.route('/test/FileUpload/form',methods=['GET'])
#Return file upload form
def upload_form():
    if 'role' in session and 'username' in session and 'user_id' in session:
        return render_template("fileupload/form.html")
    else:
        return render_template("/login/login.html", error_msg = "Please sign in first")


@webapp.route('/test/FileUpload',methods=['GET','POST'])
#Upload a new file and store in the systems temp directory
def file_upload():
    if 'role' in session and 'username' in session and 'user_id' in session:
        #get user_id from session
        user_id = session['user_id']
        # check if the post request has the file part

        if request.method == 'POST':
            # check if the post request has the file part
            if 'uploadedfile' not in request.files:
                return render_template('/fileupload/form.html', error_msg="Missing uploaded file")
            # get image file
            new_file = request.files['uploadedfile']
            # check if image name is empty
            if new_file.filename == '':
                return render_template('/fileupload/form.html', error_msg='Missing file name')
            # save image
            if new_file and allowed_file(new_file.filename):
                uploadImgName = str(user_id) + datetime.now().strftime("%m%d%Y%H%M%S") + secure_filename(new_file.filename)
                new_file.save(os.path.join(webapp.config['APP_PATH'], 'static/', uploadImgName))
            else:
                return render_template('/fileupload/form.html', error_msg='Wrong file type')

        if request.method == 'GET':
            if request.args.get('imageUrl') == '':
                return render_template('/fileupload/form.html', error_msg="Missing uploaded file")
            try:
                headers = {
                    "Range": "bytes=0-10",
                    "User-Agent": "MyTestAgent",
                    "Accept": "*/*"
                }
                req = urllib2.Request(request.args.get('imageUrl'), headers=headers)
                gcontext = ssl.SSLContext()
                response = urllib2.urlopen(req)
            except Exception:
                return render_template('/fileupload/form.html', error_msg="Invalid Url link")
            mimetype, encoding = mimetypes.guess_type(request.args.get('imageUrl'))
            if not ((mimetype and mimetype.startswith('image')) and response.code in range(200, 209)):
                return render_template('/fileupload/form.html', error_msg="Invalid Image Url")

            # get image from Url
            r = requests.get(request.args.get('imageUrl'))
            # set Url image name
            uploadImgName = str(user_id) + datetime.now().strftime("%m%d%Y%H%M%S") + request.args.get('imageUrl').split('/')[-1]
            # save image
            with open(webapp.config['APP_PATH'] + 'static/' + uploadImgName, 'wb') as f:
                f.write(r.content)


        
        # A1 codes starts
        # save upload image
        # TODO add userID before timestamp /done
        
        # check image size
        if os.stat(webapp.config['APP_PATH'] + 'static/' + uploadImgName).st_size > (64 * 1024 * 1024):
            os.system('rm ' + webapp.config['APP_PATH'] + 'static/' + uploadImgName)
            return render_template('/fileupload/form.html', error_msg="File too large")
            
        # change cwd for linux command execution
        os.chdir(webapp.config['APP_PATH'] + 'FaceMaskDetection/')
        # run image test
        cmd = 'python3 pytorch_test.py --img-path ../static/' + uploadImgName
        os.system(cmd)
        # image_class stores image class information: [#green, #red]
        f = open(webapp.config['APP_PATH'] + "FaceMaskDetection/tmp/img_info.txt", "r")
        image_class = [0, 0]
        image_info = f.readline()
        image_info_list = image_info.split('[')
        for i in range(len(image_info_list)-1):
            if image_info_list[i+1][0] == '0':
                image_class[0] += 1
            elif image_info_list[i+1][0] == '1':
                image_class[1] += 1
        f.close()
        # determine image category
        image_category = 0
        image_class_str = ''
        # no face detected
        if (image_class[0] == 0) and (image_class[1] == 0):
            image_category = 1
            image_class_str = 'no face detected'
        # all wearing masks
        elif (not image_class[0] == 0) and (image_class[1] == 0):
            image_category = 2
            image_class_str = 'all wearing masks'
        # no one wearing mask
        elif (image_class[0] == 0) and (not image_class[1] == 0):
            image_category = 3
            image_class_str = 'no one wearing mask'
        # some faces wearing masks
        elif (not image_class[0] == 0) and (not image_class[1] == 0):
            image_category = 4
            image_class_str = 'some faces wearing masks'
        # delete temporary files
        os.system('rm tmp/img_info.txt')
        os.system('mv tmp/test_' + uploadImgName + ' ../static/test_' + uploadImgName)
        # fetch test image name
        testImgName = 'test_' + uploadImgName
        image_path = os.path.join(webapp.config['APP_PATH'],'static/', uploadImgName)
        print(image_path)
        # save to database
        cnx = get_db()

        cursor = cnx.cursor()

        query = "INSERT INTO tbl_image(image_id, user_id, image_path, image_tag) VALUES(%s, %s, %s, %s)"
        cursor.execute(query, (uploadImgName, user_id, image_path, image_category))
        cnx.commit()

        return render_template('/fileupload/view.html', img = testImgName, description = image_class_str)
        # A1 codes ends

    else:
        return render_template("/login/login.html", error_msg = "Please sign in first")


@webapp.route('/api/upload', methods = ['POST'])
def test_api():
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
        error_msg = "You must put in a password!"
        rsp = {"success":"false", 
               "error": {
                   "code": 400,
                   "message": error_msg
               }}
        return jsonify(rsp), 400
        
    if 'file' not in request.files:
        error_msg = "Missing uploaded file"
        rsp = {"success": "false", 
               "error": {
                   "code": 400,
                   "message": error_msg
               }}
        return jsonify(rsp), 400
    
    cnx = get_db()

    cursor = cnx.cursor()

    query = "SELECT password, user_id FROM tbl_user_info WHERE user_name = %s"
    cursor.execute(query, (username,))

    row = cursor.fetchone()

    if not row:
        error_msg = "User does not exist."
        rsp = {"success": "false", 
               "error": {
                   "code": 401,
                   "message": error_msg
               }}
        return jsonify(rsp), 401
    else:
        verified_password = row[0]

    if (sha256_crypt.verify(password, verified_password) == False):
        error_msg = "The password you provided was incorrect."
        rsp = {"success": "false", 
               "error": {
                   "code": 401,
                   "message": error_msg
               }}
        return jsonify(rsp), 401

    new_file = request.files['file']

    # if user does not select file, browser also
    # submit a empty part without filename
    if new_file.filename == '':
        error_msg = "Missing file name"
        rsp = {"success": "false", 
               "error": {
                   "code": 400,
                   "message": error_msg
               }}
        return jsonify(rsp), 400
    
    user_id = row[1]
    # TODO add userID before timestamp /done

    if new_file and allowed_file(new_file.filename):
        uploadImgName = str(user_id) + datetime.now().strftime("%m%d%Y%H%M%S") + secure_filename(new_file.filename)
    else:
        error_msg = "Wrong file type"
        rsp = {"success": "false",
               "error": {
                   "code": 400,
                   "message": error_msg
               }}
        return jsonify(rsp), 400

    new_file.save(os.path.join(webapp.config['APP_PATH'],'static/', uploadImgName))
    # check image size
    if os.stat(webapp.config['APP_PATH'] + 'static/' + uploadImgName).st_size > (64 * 1024 * 1024):
        os.system('rm ' + webapp.config['APP_PATH'] + 'static/' + uploadImgName)
        error_msg = "File too large"
        rsp = {"success": "false", 
               "error": {
                   "code": 413,
                   "message": error_msg
               }}
        return jsonify(rsp), 413
        
    # change cwd for linux command execution
    os.chdir(webapp.config['APP_PATH'] + 'FaceMaskDetection/')
    # run image test
    cmd = 'python3 pytorch_test.py --img-path ../static/' + uploadImgName
    os.system(cmd)
    # image_class stores image class information: [#green, #red]
    f = open(webapp.config['APP_PATH'] + "FaceMaskDetection/tmp/img_info.txt", "r")
    image_class = [0, 0]
    image_info = f.readline()
    image_info_list = image_info.split('[')
    for i in range(len(image_info_list)-1):
	    if image_info_list[i+1][0] == '0':
	        image_class[0] += 1
	    elif image_info_list[i+1][0] == '1':
	        image_class[1] += 1
    f.close()
    # determine image category
    image_category = 0
    image_class_str = ''
    # no face detected
    if (image_class[0] == 0) and (image_class[1] == 0):
        image_category = 1
        image_class_str = 'no face detected'
    # all wearing masks
    elif (not image_class[0] == 0) and (image_class[1] == 0):
        image_category = 2
        image_class_str = 'all wearing masks'
    # no one wearing mask
    elif (image_class[0] == 0) and (not image_class[1] == 0):
        image_category = 3
        image_class_str = 'no one wearing mask'
    # some faces wearing masks
    elif (not image_class[0] == 0) and (not image_class[1] == 0):
        image_category = 4
        image_class_str = 'some faces wearing masks'
    # delete temporary files
    os.system('rm tmp/img_info.txt')
    os.system('mv tmp/test_' + uploadImgName + ' ../static/test_' + uploadImgName)
    num_faces = image_class[0] + image_class[1]

    image_path = os.path.join(webapp.config['APP_PATH'],'static/', uploadImgName)
    # store in database
    cnx = get_db()

    cursor = cnx.cursor()
    # print(image_path)

    query = "INSERT INTO tbl_image(image_id, user_id, image_path, image_tag) VALUES(%s, %s, %s, %s)"
    cursor.execute(query, (uploadImgName, user_id, image_path, image_category))
    cnx.commit()
    
    rsp = {"success": "true",
            "payload": {
                        "num_faces": num_faces,
                        "num_masked": image_class[0],
                        "num_unmasked": image_class[1]
                        }
            }
    return jsonify(rsp), 201