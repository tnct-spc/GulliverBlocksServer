from flask import Blueprint
import bugsnag


api_app = Blueprint('api_app', __name__)


@api_app.route('/')
def test():
    return "HelloWorld"
