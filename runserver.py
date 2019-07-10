from api import app
import bugsnag
from settings import BUGSNAG_API_KEY


if __name__ == "__main__":
    bugsnag.configure(
        api_key=BUGSNAG_API_KEY,
        project_root=".",
        release_stage = "development",
    )

    app.run(debug=True)
