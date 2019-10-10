from api._db import db
from api.models import Block, Map, Merge, MergeMap, RealSense, Pattern, PatternBlock
from datetime import datetime

lis = [[0,0,0]]

print("csv x,y,z, colorID\nx,y,z, colorID...")
while True:
    ins = input()
    if len(ins) < 3:
        break
    lis.append(list(map(int, ins.split(","))))
del lis[0]

map_id = db.session.query(Map).order_by(Map.id.desc()).first().id
count = 0
for i in range(len(lis)):
    if i % 6 == 0:
        count += 1
    x,y,z,cid = lis[i]
    block = Block(x=x,y=y,z=z,colorID=str(cid), time=datetime.now().timestamp()  + 100* count, map_id=map_id)
    db.session.add(block)
    db.session.commit()

"""
for x,y,z,cid in lis:
    block = Block(x=x,y=y,z=z,colorID=str(cid), time=datetime.now().timestamp(), map_id=map_id)
    db.session.add(block)
    db.session.commit()
"""
