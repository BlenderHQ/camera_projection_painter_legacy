# <pep8 compliant>

import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    PointerProperty
)


class BindImageHistory(PropertyGroup):
    image: PointerProperty(
        type = bpy.types.Image, name = "Image",
        options = {'HIDDEN'})


class CameraProperties(PropertyGroup):
    @property
    def available(self):
        image = self.id_data.cpp.image
        if not image:
            return False
        if image.cpp.invalid:
            return False
        return True

    def _image_update(self, context):
        camera = self.id_data
        bind_history = camera.cpp_bind_history
        images = [n.image for n in bind_history]
        if self.image not in images:
            item = camera.cpp_bind_history.add()
            item.image = self.image
            check_index = len(camera.cpp_bind_history) - 1
        else:
            check_index = images.index(self.image)

        item = bind_history[self.active_bind_index]
        if item.image != self.image:
            self.active_bind_index = check_index

    def _active_bind_index_update(self, context):
        camera = self.id_data
        bind_history = camera.cpp_bind_history
        item = bind_history[self.active_bind_index]
        if item.image != self.image:
            self.image = item.image

    active_bind_index: IntProperty(
        name = "Active Bind History Index",
        default = 0,
        update = _active_bind_index_update)

    image: PointerProperty(
        type = bpy.types.Image, name = "Image",
        options = {'HIDDEN'},
        description = "An image binded to a camera for use as a Clone Image in Texture Paint mode",
        update = _image_update)

    use_calibration: BoolProperty(
        name = "Calibration", default = False,
        options = {'HIDDEN'},
        description = "Use camera calibration")

    calibration_principal_point: FloatVectorProperty(
        name = "Principal Point",
        size = 2,
        default = (0.0, 0.0),
        step = 0.0001,
        precision = 6,
        subtype = 'TRANSLATION',
        unit = 'CAMERA',
        options = {'HIDDEN'},
        description = "A point at the intersection of the optical axis and the image plane."
                      "This point is referred to as the principal point or image center")

    calibration_skew: FloatProperty(
        name = "Skew",
        default = 0.0, step = 0.001, precision = 6, soft_min = -1.0, soft_max = 1.0,
        subtype = 'FACTOR',
        options = {'HIDDEN'},
        description = "")

    calibration_aspect_ratio: FloatProperty(
        name = "Aspect Ratio",
        default = 0.0, step = 0.001, precision = 6, soft_min = -1.0, soft_max = 1.0,
        subtype = 'FACTOR',
        options = {'HIDDEN'},
        description = "")

    lens_distortion_radial_1: FloatProperty(
        name = "Radial 1",
        default = 0.0, step = 0.001, precision = 6, soft_min = -1.0, soft_max = 1.0,
        subtype = 'FACTOR',
        options = {'HIDDEN'},
        description = "")

    lens_distortion_radial_2: FloatProperty(
        name = "Radial 2",
        default = 0.0, step = 0.001, precision = 6, soft_min = -1.0, soft_max = 1.0,
        subtype = 'FACTOR',
        options = {'HIDDEN'},
        description = "")

    lens_distortion_radial_3: FloatProperty(
        name = "Radial 3",
        default = 0.0, step = 0.001, precision = 6, soft_min = -1.0, soft_max = 1.0,
        subtype = 'FACTOR',
        options = {'HIDDEN'},
        description = "")

    lens_distortion_tangential_1: FloatProperty(
        name = "Tangential 1",
        default = 0.0, step = 0.001, precision = 6, soft_min = -1.0, soft_max = 1.0,
        subtype = 'FACTOR',
        options = {'HIDDEN'},
        description = "")

    lens_distortion_tangential_2: FloatProperty(
        name = "Tangential 2",
        default = 0.0, step = 0.001, precision = 6, soft_min = -1.0, soft_max = 1.0,
        subtype = 'FACTOR',
        options = {'HIDDEN'},
        description = "")
