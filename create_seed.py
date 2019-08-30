from api._db import db
from api.models import Block, Map, Merge, MergeMap, RealSense, Pattern, PatternBlock
from datetime import datetime

if __name__ == "__main__":
    map = Map()
    map.name = "test_map"
    db.session.add(map)
    db.session.commit()

    merge = Merge(name="test")
    db.session.add(merge)
    db.session.commit()

    merge_map = MergeMap(x=0, y=0, rotate=0, map_id=map.id, merge_id=merge.id)
    db.session.add(merge_map)

    realsense = RealSense(name='test_realsense', current_map_id=map.id)
    db.session.add(realsense)

    pattern = Pattern(
        name="road",
        extend_to_right=False,
        extend_to_left=False,
        extend_to_top=True,
        extend_to_bottom=True
    )
    db.session.add(pattern)
    db.session.commit()

    blocks = [
        Block(x=1, y=2, z=3, colorID="1", time=datetime.now().timestamp(), map_id=map.id),
        Block(x=1, y=3, z=3, colorID="1", time=datetime.now().timestamp(), map_id=map.id),
        Block(x=2, y=2, z=3, colorID="1", time=datetime.now().timestamp(), map_id=map.id),
        Block(x=1, y=2, z=4, colorID="1", time=datetime.now().timestamp(), map_id=map.id),
        Block(x=1, y=2, z=2, colorID="1", time=datetime.now().timestamp(), map_id=map.id),
        Block(x=1, y=2, z=1, colorID="9", time=datetime.now().timestamp(), map_id=map.id),
        Block(x=2, y=2, z=1, colorID="0", time=datetime.now().timestamp(), map_id=map.id),
        Block(x=3, y=2, z=1, colorID="0", time=datetime.now().timestamp(), map_id=map.id),
        Block(x=4, y=2, z=1, colorID="9", time=datetime.now().timestamp(), map_id=map.id)
    ]
    for block in blocks:
        db.session.add(block)
    pattern_blocks = [
        PatternBlock(x=0, y=0, z=0, colorID="9", pattern_id=pattern.id),
        PatternBlock(x=1, y=0, z=0, colorID="0", pattern_id=pattern.id),
        PatternBlock(x=2, y=0, z=0, colorID="0", pattern_id=pattern.id),
        PatternBlock(x=3, y=0, z=0, colorID="9", pattern_id=pattern.id)
    ]
    for pattern_block in pattern_blocks:
        db.session.add(pattern_block)

    try:
        db.session.commit()
    except:
        print('integrity error')
        db.session.rollback()
