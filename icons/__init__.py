import bpy
import os

ICON_EXT = "png"
_preview_collection = {}


def get_icon_id(key):
    return _preview_collection["main"][key].icon_id


def register():
    import bpy.utils.previews
    pcoll = bpy.utils.previews.new()
    icons_dir = os.path.dirname(__file__)

    for file_name in os.listdir(icons_dir):
        name, ext = os.path.splitext(file_name)
        if ext == "." + ICON_EXT:
            pcoll.load(name, os.path.join(icons_dir, file_name), 'IMAGE')
    _preview_collection["main"] = pcoll


def unregister():
    for pcoll in _preview_collection.values():
        bpy.utils.previews.remove(pcoll)
    _preview_collection.clear()


register()
