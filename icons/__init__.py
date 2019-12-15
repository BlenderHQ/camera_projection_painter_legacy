# <pep8 compliant>

import os

_preview_collection = None


def get_icon_id(key):
    global _preview_collection
    if _preview_collection is None:
        import bpy.utils.previews
        _preview_collection = bpy.utils.previews.new()
    if key not in _preview_collection:
        path = os.path.join(os.path.dirname(__file__), "%s.png" % key)
        _preview_collection.load(key, path, "IMAGE")
    if key in _preview_collection:
        return _preview_collection[key].icon_id
    return 0


def unregister():
    if _preview_collection is not None:
        import bpy.utils.previews
        bpy.utils.previews.remove(_preview_collection)
