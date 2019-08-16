import os
from flask import Flask, redirect
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_sqlalchemy import SQLAlchemy
from api.models import *
from settings import DATABASE_URL


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'redis'
app.config['SECRET_KEY'] = os.urandom(24)

db = SQLAlchemy(app)

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
