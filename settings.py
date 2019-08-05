import os
from dotenv import load_dotenv


load_dotenv(verbose=True)

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

FLASK_ENV = os.environ.get("FLASK_ENV")
DATABASE_URL = os.environ.get("DATABASE_URL")
REDIS_URL = os.environ.get("REDIS_URL")
