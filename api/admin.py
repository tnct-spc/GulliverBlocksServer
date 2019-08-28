from api._app import app
from api._db import db
from flask import redirect
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from api.models import *


admin = Admin(app, name='GulliverBlocksServer', template_mode='bootstrap3')


class GBModelView(ModelView):
    def is_accessible(self):
        return True # TO-DO login必須にする

    def inaccessible_callback(self, name, **kwargs):
        return redirect('/')


admin.add_view(ModelView(Block, db.session))
admin.add_view(ModelView(Map, db.session))
admin.add_view(ModelView(RealSense, db.session))
admin.add_view(ModelView(Merge, db.session))
admin.add_view(ModelView(MergeMap, db.session))
admin.add_view(ModelView(ColorRule, db.session))
admin.add_view(ModelView(Pattern, db.session))
admin.add_view(ModelView(PatternBlock, db.session))
