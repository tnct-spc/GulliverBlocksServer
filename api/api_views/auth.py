from flask import Blueprint, make_response, request, session, redirect
from api.models import User
from api._db import db


auth_api_app = Blueprint("auth_api_app", __name__)


def login_required(func):
    def new_func(*args, **kwargs):
        try:
            request.cookies["user_id"]
        except KeyError:
            return make_response("you are not logged in")
        result = func(*args, **kwargs)
        return result
    return new_func


@auth_api_app.route("/login/", methods=["POST"])
def login():
    if request.content_type == "application/json":
        username = request.json["username"]
        password = request.json["password"]
        user = db.session.query(User).filter_by(username=username).first()
        if user:
            if user.auth_password(password):
                session["username"] = username
                response = make_response("ok")
                response.set_cookie("user_id", user.id)
                return response, 200
        return make_response("invalid username or password"), 401
    else:
        return make_response('content type must be application/app'), 406


@auth_api_app.route("/logout/")
def logout():
    response = make_response("ok")
    response.set_cookie("user_id", "", expires=0)
    return response, 200


@auth_api_app.route("/debug_login/", methods=["GET", "POST"])
def debug_login():
    if request.method == "GET":
        return make_response(
            '<!DOCTYPE html>'
            '<html>' +
            '<body>' +
            '   <p>LOGIN</p>' +
            '   <form method="post", action="">' +
            '       <input type="text" name="username">' +
            '       <input type="text" name="password">' +
            '       <input type="submit">' +
            '   </form>' +
            '</body>' +
            '</html>'
        )
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = db.session.query(User).filter_by(username=username).first()
        if user:
            if user.auth_password(password):
                response = make_response(redirect("/admin/"))
                response.set_cookie("user_id", str(user.id))
                return make_response(response), 200
        return make_response(
            '<!DOCTYPE html>'
            '<html>' +
            '<body>' +
            '   <p style="color: red;">invalid username or password</p>'
            '   <p>LOGIN</p>' +
            '   <form method="post", action="">' +
            '       <input type="text" name="username">' +
            '       <input type="text" name="password">' +
            '       <input type="submit">' +
            '   </form>' +
            '</body>' +
            '</html>'
        )
