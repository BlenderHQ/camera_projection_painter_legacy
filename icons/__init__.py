# <pep8 compliant>

# Icon ids are available as icons.get_icon_id ("icon_key"), where "icon_key" is the name of the file name.
# without extension inside the module directory. All previews are loaded into the collection
# during the registration method call to avoid delayed loading of icons with a delay


import bpy.utils.previews
import os

ICON_EXTENSIONS = (".png",)

if "_preview_collection" not in locals():  # In case of module reloading
    _preview_collection = None


def get_icon_id(key):
    """
    Returns the identifier of an icon_id from existing image files in the module directory
    @param key: str - File name without extension
    @return: int - icon_id
    """
    if _preview_collection and key in _preview_collection:
        return _preview_collection[key].icon_id
    return 0


def register():
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
