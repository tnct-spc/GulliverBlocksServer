from flask import Blueprint, make_response, request, redirect
from api.models import Share, User, ViewRight
from api.api_views.auth import login_required
from api._db import db


share_api_app = Blueprint("share_api_app", __name__)


@share_api_app.route("/create_share/", methods=["POST"])
def create_share():
    if request.content_type == "application/json":
        try:
            map_or_merge_id = request.json["map_or_merge_id"]
        except KeyError:
            return make_response("map_or_merge_id missing"), 400

        db.session.add(Share(map_or_merge_id=map_or_merge_id))
        try:
            db.session.commit()
        except:
            return make_response('integrity error'), 500
        return make_response("ok"), 200
    else:
        return make_response('content type must be application/app'), 406


@share_api_app.route("/receive_share/<uuid:share_id>/")
@login_required
def get_share(user, share_id):
    share = db.session.query(Share).filter_by(id=share_id).first()
    # まだ対応するview_rightがなかったら生成する
    if not db.session.query(ViewRight).filter_by(
            user_id=user.id,
            map_or_merge_id=share.map_or_merge_id).first():
        db.session.add(ViewRight(user_id=user.id, map_or_merge_id=share.map_or_merge_id))
        try:
            db.session.commit()
        except:
            return make_response('integrity error'), 500

    return make_response(redirect("/"))
