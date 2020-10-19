from flask import render_template, redirect, url_for, request
from app import webapp

from datetime import datetime
import time
import tempfile
import os
import requests
import mimetypes
import urllib.request as urllib2


@webapp.route('/test/FileUpload/form',methods=['GET'])
#Return file upload form
def upload_form():
    return render_template("fileupload/form.html")


@webapp.route('/test/FileUpload',methods=['GET','POST'])
#Upload a new file and store in the systems temp directory
def file_upload():
    # check if the post request has the file part
    if ('uploadedfile' not in request.files) and (request.args.get('imageUrl') == ''):
        return "Missing uploaded file"
    
    if 'uploadedfile' in request.files:
        new_file = request.files['uploadedfile']
        # if user does not select file, browser also
        # submit a empty part without filename
        if new_file.filename == '':
            return 'Missing file name'
        # set upload image name
        uploadImgName = datetime.now().strftime("%m%d%Y%H%M%S") + new_file.filename
        # save image
        new_file.save(os.path.join(webapp.config['APP_PATH'],'Upload_Image/', uploadImgName))
    else:
        # validate image Url
        try:
            headers = {
                "Range": "bytes=0-10",
                "User-Agent": "MyTestAgent",
                "Accept": "*/*"
            }
            req = urllib2.Request(request.args.get('imageUrl'), headers=headers)
            response = urllib2.urlopen(req)
        except Exception:
            return "Invalid Url link"
        mimetype, encoding = mimetypes.guess_type(request.args.get('imageUrl'))
        if not ((mimetype and mimetype.startswith('image')) and response.code in range(200, 209)):
            return "Invalid Image Url"
        
        # get image from Url
        r = requests.get(request.args.get('imageUrl'))
        # set Url image name
        uploadImgName = datetime.now().strftime("%m%d%Y%H%M%S") + request.args.get('imageUrl').split('/')[-1]
        # save image
        with open(webapp.config['APP_PATH'] + 'Upload_Image/' + uploadImgName, 'wb') as f:
            f.write(r.content)
        
    # A1 codes starts
    # check image size
    if os.stat(webapp.config['APP_PATH'] + 'Upload_Image/' + uploadImgName).st_size > (64 * 1024 * 1024):
        os.system('rm ' + webapp.config['APP_PATH'] + 'Upload_Image/' + uploadImgName)
        return 'File too large'
        
    # change cwd for linux command execution
    os.chdir(webapp.config['APP_PATH'] + 'FaceMaskDetection/')
    # run image test
    cmd = 'python3 pytorch_test.py --img-path ../Upload_Image/' + uploadImgName
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
    return render_template('/fileupload/view.html', img = testImgName, category = image_category, description = image_class_str)
    # A1 codes ends


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
        error_msg = "You must put in an email address!"
        rsp = {"success":"false", 
               "error": {
                   "code": 400,
                   "message": error_msg
               }}
        return jsonify(rsp), 400
        
    if 'uploadedfile' not in request.files:
        error_msg = "Missing uploaded file"
        rsp = {"success": "false", 
               "error": {
                   "code": 400,
                   "message": error_msg
               }}
        return jsonify(rsp), 400
    
    new_file = request.files['uploadedfile']

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
    
    
    
    
    
    
    
    # TODO add userID before timestamp
    uploadImgName = datetime.now().strftime("%m%d%Y%H%M%S") + new_file.filename





    
    
    
    new_file.save(os.path.join(webapp.config['APP_PATH'],'Upload_Image/', uploadImgName))
    # check image size
    if os.stat(webapp.config['APP_PATH'] + 'Upload_Image/' + uploadImgName).st_size > (64 * 1024 * 1024):
        os.system('rm ' + webapp.config['APP_PATH'] + 'Upload_Image/' + uploadImgName)
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
    cmd = 'python3 pytorch_test.py --img-path ../Upload_Image/' + uploadImgName
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
    
    rsp = {"success": "true",
            "payload": {
                        "num_faces": num_faces,
                        "num_masked": image_class[0],
                        "num_unmasked": image_class[1]
                        }
            }
    return jsonify(rsp), 201