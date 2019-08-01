from api import app
from settings import FLASK_ENV
import os


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(host = '0.0.0.0', port = port, debug=True)
