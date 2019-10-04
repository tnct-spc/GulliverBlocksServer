from api._app import app
from api._db import db
from flask import redirect, session
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from api.models import *


admin = Admin(app, name='GulliverBlocksServer', template_mode='bootstrap3')


class GBModelView(ModelView):
    column_display_pk = True

    def __init__(self, model, session, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        super(GBModelView, self).__init__(model, session)

    def is_accessible(self):
        try:
            session["user_id"]
        except KeyError:
            return False
        return True

    def inaccessible_callback(self, name, **kwargs):
        return redirect('/')


class BlockModelView(GBModelView):
    def create_form(self):
        form = super(BlockModelView, self).create_form()
        if form.pattern_group_id.data == "":
            form.pattern_group_id.data = None
        return form


admin.add_view(BlockModelView(Block, db.session, column_filters=["map"]))
admin.add_view(GBModelView(Map, db.session))
admin.add_view(GBModelView(RealSense, db.session))
admin.add_view(GBModelView(Merge, db.session))
admin.add_view(GBModelView(MergeMap, db.session, column_filters=["merge"]))
admin.add_view(GBModelView(ColorRule, db.session, column_filters=["map"]))
admin.add_view(GBModelView(Pattern, db.session))
admin.add_view(GBModelView(PatternBlock, db.session, column_filters=["pattern"]))
admin.add_view(GBModelView(User, db.session, column_filters=["username"]))
admin.add_view((GBModelView(ViewRight, db.session, column_filters=["user"])))
