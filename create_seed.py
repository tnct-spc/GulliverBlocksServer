from api._db import db
from api.models import Block
from datetime import datetime


if __name__ == "__main__":
    blocks = [
        Block(block_id=1, x=1, y=2, z=3, colorID=1, put=True, time=datetime.now().timestamp()),
        Block(block_id=2, x=1, y=3, z=3, colorID=1, put=True, time=datetime.now().timestamp()),
        Block(block_id=3, x=2, y=2, z=3, colorID=1, put=True, time=datetime.now().timestamp()),
        Block(block_id=4, x=1, y=2, z=4, colorID=1, put=True, time=datetime.now().timestamp()),
        Block(block_id=5, x=1, y=2, z=2, colorID=1, put=True, time=datetime.now().timestamp())
    ]

    for block in blocks:
        db.session.add(block)

    try:
        db.session.commit()
    except:
        print("error")
        db.session.rollback()
