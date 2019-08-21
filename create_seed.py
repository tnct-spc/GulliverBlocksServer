from api._app import db
from api.models import Block, Map, Merge, MergeMap, RealSense, Pattern, PatternBlock
from datetime import datetime

if __name__ == "__main__":
    map = Map()
    map.name = "test_map"
    db.session.add(map)
    db.session.commit()
    realsense = RealSense(name='test_realsense', current_map_id=map.id)
    db.session.add(realsense)
    db.session.commit()
    blocks = [
        Block(x=1, y=2, z=3, colorID="1", time=datetime.now().timestamp(), map_id=map.id),
        Block(x=1, y=3, z=3, colorID="1", time=datetime.now().timestamp(), map_id=map.id),
        Block(x=2, y=2, z=3, colorID="1", time=datetime.now().timestamp(), map_id=map.id),
        Block(x=1, y=2, z=4, colorID="1", time=datetime.now().timestamp(), map_id=map.id),
        Block(x=1, y=2, z=2, colorID="1", time=datetime.now().timestamp(), map_id=map.id)
    ]
    for block in blocks:
        db.session.add(block)
    pattern = Pattern(name="road")
    pattern_blocks = [
        PatternBlock(x=0, y=0, z=0, colorID="white", pattern_id=pattern.id),
        PatternBlock(x=1, y=0, z=0, colorID="white", pattern_id=pattern.id),
        PatternBlock(x=2, y=0, z=0, colorID="white", pattern_id=pattern.id),
        PatternBlock(x=3, y=0, z=0, colorID="white", pattern_id=pattern.id)
    ]
    for pattern_block in pattern_blocks:
        db.session.add(pattern_block)
    try:
        db.session.commit()
    except:
        print('integrity error')
        db.session.rollback()
