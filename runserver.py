from api import app
import bugsnag
from settings import BUGSNAG_API_KEY
import os


if __name__ == "__main__":
    bugsnag.configure(
        api_key=BUGSNAG_API_KEY,
        project_root=".",
        release_stage = "FLASK_ENV",
    )
    port = int(os.environ.get("PORT", 5000))

    app.run(host = '0.0.0.0', port = port, debug=True)
