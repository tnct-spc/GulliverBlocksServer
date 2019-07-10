import bugsnag
from settings import BUGSNAG_API_KEY


bugsnag.configure(
    api_key=BUGSNAG_API_KEY,
    project_root="."
)
