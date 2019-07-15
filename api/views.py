from flask import Blueprint, make_response, jsonify
from datetime import datetime


api_app = Blueprint('api_app', __name__)


@api_app.route('/return_test_data/')
def return_test_data():
    test_data = {
"blocks":[
{
"ID":1,
"colorID":1,
"put":True,
"time":1562920187.972499,
"x":1,
"y":2,
"z":3
},
{
"ID":2,
"colorID":1,
"put":True,
"time":1562920187.97251,
"x":1,
"y":3,
"z":3
},
{
"ID":3,
"colorID":1,
"put":True,
"time":1562920187.972519,
"x":2,
"y":2,
"z":3
},
{
"ID":4,
"colorID":1,
"put":True,
"time":1562920187.972523,
"x":1,
"y":2,
"z":4
},
{
"ID":5,
"colorID":1,
"put":True,
"time":1562920187.972528,
"x":1,
"y":2,
"z":2
}
]
}
    
    return make_response(jsonify(test_data))
