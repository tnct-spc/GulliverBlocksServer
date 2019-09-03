from api._app import app
from api._db import db
from flask import redirect
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from api.models import *


admin = Admin(app, name='GulliverBlocksServer', template_mode='bootstrap3')


class GBModelView(ModelView):
    column_display_pk = True

    def is_accessible(self):
        return True # TO-DO login必須にする

    def inaccessible_callback(self, name, **kwargs):
        return redirect('/')


admin.add_view(GBModelView(Block, db.session))
admin.add_view(GBModelView(Map, db.session))
admin.add_view(GBModelView(RealSense, db.session))
admin.add_view(GBModelView(Merge, db.session))
admin.add_view(GBModelView(MergeMap, db.session))
admin.add_view(GBModelView(ColorRule, db.session))
admin.add_view(GBModelView(Pattern, db.session))
admin.add_view(GBModelView(PatternBlock, db.session))
