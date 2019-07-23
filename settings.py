import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from api import app


load_dotenv(verbose=True)

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

BUGSNAG_API_KEY = os.environ.get("BUGSNAG_API_KEY")
FLASK_ENV = os.environ.get("FLASK_ENV")
