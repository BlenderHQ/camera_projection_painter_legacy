# <pep8 compliant>

import bpy.utils.previews
import os

ICON_EXTENSIONS = (".png",)

if "_preview_collection" not in locals():
    _preview_collection = None


def get_icon_id(key):
    if _preview_collection and key in _preview_collection:
        return _preview_collection[key].icon_id
    return 0


def register():
    # Load all previews into the collection at once in order
    # to eliminate the often observed loading of icons with a delay

    global _preview_collection

    if _preview_collection is None:
        _preview_collection = bpy.utils.previews.new()

    directory_path = os.path.dirname(__file__)
    for filename in os.listdir(directory_path):
        filepath = os.path.join(directory_path, filename)
        if os.path.isfile(filepath):
            name, ext = os.path.splitext(filename)
            if ext not in ICON_EXTENSIONS:
                continue
            _preview_collection.load(name, filepath, "IMAGE")


def unregister():
    global _preview_collection

    if _preview_collection is not None:
        bpy.utils.previews.remove(_preview_collection)
        _preview_collection = None
