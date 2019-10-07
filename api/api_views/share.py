from flask import Blueprint, make_response, request, redirect
from api.models import ViewRight, Map, Merge
from api.api_views.user import login_required
from api._db import db


share_api_app = Blueprint("share_api_app", __name__)


@share_api_app.route("/receive_share/<uuid:map_or_merge_id>/")
@login_required
def receive_share(user, map_or_merge_id):
    # まだ対応するview_rightがなかったら生成する
    if not db.session.query(ViewRight).filter_by(user_id=user.id, map_or_merge_id=map_or_merge_id).first():
        db.session.add(ViewRight(user_id=user.id, map_or_merge_id=map_or_merge_id))
        try:
            db.session.commit()
        except:
            return make_response('integrity error'), 500

    return make_response("ok"), 200


@share_api_app.route("/share/<uuid:map_or_merge_id>/")
def share(map_or_merge_id):
    if db.session.query(Map).filter_by(id=map_or_merge_id).first():
        return redirect("gulliverblocks://map/" + str(map_or_merge_id))
    elif db.session.query(Merge).filter_by(id=map_or_merge_id).first():
        return redirect("gulliverblocks://merge/" + str(map_or_merge_id))
    else:
        return make_response("this world not found"), 404
