from flask import Flask
webapp = Flask(__name__)

from app import main
from app import fileupload

webapp.config['APP_PATH'] = '/home/ubuntu/Desktop/A1/app/'