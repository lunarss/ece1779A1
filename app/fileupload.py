from flask import render_template, redirect, url_for, request
from app import webapp

import tempfile
import os


@webapp.route('/test/FileUpload/form',methods=['GET'])
#Return file upload form
def upload_form():
    return render_template("fileupload/form.html")


@webapp.route('/test/FileUpload',methods=['POST'])
#Upload a new file and store in the systems temp directory
def file_upload():
    userid = request.form.get("userID")
    passowrd = request.form.get("password")

    # check if the post request has the file part
    if 'uploadedfile' not in request.files:
        return "Missing uploaded file"

    new_file = request.files['uploadedfile']

    # if user does not select file, browser also
    # submit a empty part without filename
    if new_file.filename == '':
        return 'Missing file name'

    # A1 codes starts
    # save upload image
    path = '/home/ubuntu/Desktop/A1/app/'
    new_file.save(os.path.join(path,'Upload_Image/',new_file.filename))
    # change cwd for linux command execution
    os.chdir(path + 'FaceMaskDetection/')
    # run image test
    cmd = 'python3 pytorch_test.py --img-path ../Upload_Image/' + new_file.filename
    os.system(cmd)
    # image_class stores image class information: [#green, #red]
    f = open(path + "FaceMaskDetection/tmp/img_info.txt", "r")
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
    # no face wearing mask
    if (image_class[0] + image_class[1]) == 0:
        image_category = 1
    # all wearing masks
    elif (not image_class[0] == 0) and (image_class[1] == 0):
        image_category = 2
    # no one wearing mask
    elif (image_class[0] == 0) and (not image_class[1] == 0):
        image_category = 3
    # some faces wearing masks
    elif (not image_class[0] == 0) and (not image_class[1] == 0):
        image_category = 4
    # delete temporary files
    os.system('sudo rm -rf tmp/img_info.txt')
    os.system('mv tmp/' + new_file.filename + ' ../Output_Image/' + new_file.filename)
    # fetch image path
    imgName = path + 'Output_Image/' + new_file.filename
    return render_template('/fileupload/view.html', img = imgName, category = image_category)
    # A1 codes starts


