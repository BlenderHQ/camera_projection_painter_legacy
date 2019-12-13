import os
import bpy

if "_pcoll" not in locals():
    from bpy.utils import previews

    _pcoll = previews.new()
    del previews


def get_icon_id(key):
    if key not in _pcoll:
        path = os.path.join(os.path.dirname(__file__), "%s.png" % key)
        _pcoll.load(key, path, "IMAGE")
    return _pcoll[key].icon_id


def unregister():
    bpy.utils.previews.remove(_pcoll)
