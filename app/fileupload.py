from flask import render_template, redirect, url_for, request
from app import webapp

from datetime import datetime
import time
import tempfile
import os


@webapp.route('/test/FileUpload/form',methods=['GET'])
#Return file upload form
def upload_form():
    return render_template("fileupload/form.html")


@webapp.route('/test/FileUpload',methods=['POST'])
#Upload a new file and store in the systems temp directory
def file_upload():
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
    
    


    
    
    
    
    # TODO change absolute path
    path = '/home/ubuntu/Desktop/A1/app/'
    # TODO add userID before timestamp
    uploadImgName = datetime.now().strftime("%m%d%Y%H%M%S") + new_file.filename





    
    
    
    new_file.save(os.path.join(path,'Upload_Image/', uploadImgName))
    # check image size
    if os.stat(path + 'Upload_Image/' + uploadImgName).st_size > (64 * 1024 * 1024):
        os.system('rm ' + path + 'Upload_Image/' + uploadImgName)
        return 'File too large'
        
    # change cwd for linux command execution
    os.chdir(path + 'FaceMaskDetection/')
    # run image test
    cmd = 'python3 pytorch_test.py --img-path ../Upload_Image/' + uploadImgName
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


