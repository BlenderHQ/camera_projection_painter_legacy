# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(utils)

    del importlib
else:
    from .. import utils

from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty,
)


class ImageProperties(PropertyGroup):
    preview_check_passed: BoolProperty(
        default = False,
        options = {'HIDDEN', 'SKIP_SAVE'}
    )

    @property
    def static_size(self):
        image = self.id_data
        width, height = utils.common.get_image_static_size(image)
        return width, height

    @property
    def aspect(self):
        image = self.id_data
        width, height = image.cpp.static_size

        if width > height:
            aspect_x = 1.0
            aspect_y = width / height
        elif height > width:
            aspect_x = 1.0
            aspect_y = width / height
        else:
            aspect_x = 1.0
            aspect_y = 1.0

        return aspect_x, aspect_y

    @property
    def invalid(self):
        image = self.id_data
        size_x, size_y = image.cpp.static_size
        if size_x and size_y:
            return False
        return True
