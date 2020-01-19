# <pep8 compliant>

# The module does not have a registration method. It occurs during the very first call to
# get_icon_id since for some custom properties it is necessary to access the icons at the module import stage

import bpy
import os

ICON_EXTENSIONS = (".png",)

if "_preview_collection" not in locals():  # In case of module reloading
    _preview_collection = None


def get_icon_id(key: str):
    """
    Returns the identifier of an icon_id from existing image files in the module directory
    @param key: str - File name without extension
    @return: int - icon_id
    """
    global _preview_collection

    if (_preview_collection is None):
        from bpy.utils import previews
        _preview_collection = previews.new()

        directory_path = os.path.dirname(__file__)
        for filename in os.listdir(directory_path):
            filepath = os.path.join(directory_path, filename)
            if os.path.isfile(filepath):
                name, ext = os.path.splitext(filename)
                if ext not in ICON_EXTENSIONS:
                    continue
                _preview_collection.load(name, filepath, "IMAGE")
    
    if key in _preview_collection:
        return _preview_collection[key].icon_id
    
    return 0

def unregister():
    global _preview_collection
    if not (_preview_collection is None):
        bpy.utils.previews.remove(_preview_collection)
        _preview_collection = None
