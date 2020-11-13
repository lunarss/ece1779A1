
from flask import Flask
from flask_mail import Mail, Message
from app.config import smtp_config

webapp = Flask(__name__)

# session secret key
webapp.secret_key = b'_5ks&z\i\6p#]/'

# smtp configuration
mail= Mail(webapp)

webapp.config['MAIL_SERVER']=smtp_config['MAIL_SERVER']
webapp.config['MAIL_PORT'] = smtp_config['MAIL_PORT']
webapp.config['MAIL_USERNAME'] = smtp_config['MAIL_USERNAME']
webapp.config['MAIL_PASSWORD'] = smtp_config['MAIL_PASSWORD']
webapp.config['MAIL_USE_TLS'] = smtp_config['MAIL_USE_TLS']
webapp.config['MAIL_USE_SSL'] = smtp_config['MAIL_USE_SSL']

# for Token
webapp.config['JWT_SECRET_KEY'] = 'JWT_KEY'

# for file upload path
webapp.config['APP_PATH'] = '/home/ubuntu/Desktop/Project1/app/'

from app import main
from app import login
from app import user
from app import password
from app import history
from app import fileupload
# from app import main