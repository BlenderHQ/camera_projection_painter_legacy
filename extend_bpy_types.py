# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    EnumProperty,
    StringProperty,
    PointerProperty
)

import io
import os
from .icons import get_icon_id
from .utils import utils_camera, utils_image


class CameraProperties(PropertyGroup):
    @property
    def available(self):
        return self.id_data.cpp.used and self.id_data.cpp.image

    used: BoolProperty(description = "Use camera as a projector")

    image: PointerProperty(
        type = bpy.types.Image, name = "Image",
        description = "Image for texture paint from this camera")

    use_calibration: BoolProperty(
        name = "Calibration", default = False,
        description = "Use camera calibration")

    calibration_principal_point: FloatVectorProperty(
        name = "Principal Point",
        size = 2,
        default = (0.0, 0.0),
        step = 0.0001,
        precision = 6,
        subtype = 'TRANSLATION',
        unit = 'CAMERA',
        description = "A point at the intersection of the optical axis and the image plane."
                      "This point is referred to as the principal point or image center")

    calibration_skew: FloatProperty(
        name = "Skew",
        default = 0.0, step = 0.001, precision = 6, soft_min = -1.0, soft_max = 1.0,
        subtype = 'FACTOR',
        description = "")

    calibration_aspect_ratio: FloatProperty(
        name = "Aspect Ratio",
        default = 0.0, step = 0.001, precision = 6, soft_min = -1.0, soft_max = 1.0,
        subtype = 'FACTOR',
        description = "")

    lens_distortion_radial_1: FloatProperty(
        name = "Radial 1",
        default = 0.0, step = 0.001, precision = 6, soft_min = -1.0, soft_max = 1.0,
        subtype = 'FACTOR',
        description = "")

    lens_distortion_radial_2: FloatProperty(
        name = "Radial 2",
        default = 0.0, step = 0.001, precision = 6, soft_min = -1.0, soft_max = 1.0,
        subtype = 'FACTOR',
        description = "")

    lens_distortion_radial_3: FloatProperty(
        name = "Radial 3",
        default = 0.0, step = 0.001, precision = 6, soft_min = -1.0, soft_max = 1.0,
        subtype = 'FACTOR',
        description = "")

    lens_distortion_tangential_1: FloatProperty(
        name = "Tangential 1",
        default = 0.0, step = 0.001, precision = 6, soft_min = -1.0, soft_max = 1.0,
        subtype = 'FACTOR',
        description = "")

    lens_distortion_tangential_2: FloatProperty(
        name = "Tangential 2",
        default = 0.0, step = 0.001, precision = 6, soft_min = -1.0, soft_max = 1.0,
        subtype = 'FACTOR',
        description = "")


class SceneProperties(PropertyGroup):
    @property
    def _scene(self):
        return self.id_data

    @property
    def has_visible_camera_objects(self):
        for ob in self._scene.objects:
            if ob.type != 'CAMERA':
                continue
            if ob.visible_get():
                return True
        return False

    @property
    def visible_camera_objects(self):
        return (ob for ob in self._scene.objects if (ob.type == 'CAMERA' and ob.visible_get()))

    @property
    def has_available_camera_objects(self):
        return len(list(self._scene.cpp.available_camera_objects)) != 0

    @property
    def available_camera_objects(self):
        return (ob for ob in self._scene.cpp.visible_camera_objects if ob.data.cpp.available)

    @property
    def has_camera_objects_selected(self):
        return len(list(self._scene.cpp.selected_camera_objects)) != 0

    @property
    def selected_camera_objects(self):
        return (ob for ob in self._scene.cpp.visible_camera_objects if ob.select_get())

    def _cameras_viewport_size_update(self, context):
        utils_camera.resize_cameras_viewport(context, self.cameras_viewport_size)

    source_images_path: StringProperty(
        name = "Source Images Directory", subtype = 'DIR_PATH',
        description = "Path to source images used. "
                      "If image named same as object not found in packed images, "
                      "operator search images there and open them automatically")

    calibration_source_file: StringProperty(
        name = "Camera Calibration File", subtype = 'FILE_PATH',
        description = "Path to third-party application *.csv file."
                      "Used for automatic setup camera calibration parameters")

    # Tool relative
    mapping: EnumProperty(
        items = [('UV', "UV", "Standard UV Mapping", '', 0),
                 ('CAMERA', "Camera", "Camera Projection", '', 1)],
        name = "Mapping",
        default = 'UV',
        description = "Mapping method for source image")

    # Camera section
    use_auto_set_camera: BoolProperty(
        name = "Use Automatic Camera", default = False,
        description = "Automatic/User camera selection\n"
                      "Warning! Using this option with large images may be laggy")

    use_auto_set_image: BoolProperty(
        name = "Use Automatic Image", default = True,
        description = "Automatic/User image selection")

    auto_set_camera_method: EnumProperty(
        items = [
            ('FULL', "Full",
             "Automatic dependent to world orientation and location",
             get_icon_id("autocam_full"), 0),
            ('DIRECTION', "Direction",
             "Automatic dependent to view direction only",
             get_icon_id("autocam_direction"), 1)
        ],
        name = "Auto Camera Method",
        default = 'FULL',
        description = "Method for camera selection")

    tolerance_full: FloatProperty(
        name = "Tolerance", default = 0.92, soft_min = 0.0, soft_max = 1.0,
        subtype = 'FACTOR',
        description = "Sensitivity for automatic camera selection")

    tolerance_direction: FloatProperty(
        name = "Tolerance", default = 0.55, soft_min = 0.0, soft_max = 1.0,
        subtype = 'FACTOR',
        description = "Sensitivity for automatic camera selection")

    cameras_viewport_size: FloatProperty(
        name = "Viewport Display Size",
        default = 1.0, soft_min = 1.0, soft_max = 5.0, step = 0.1,
        subtype = 'DISTANCE',
        description = "Viewport cameras display size",
        update = _cameras_viewport_size_update)

    # Viewport draw
    use_projection_preview: BoolProperty(
        name = "Projection Preview", default = True,
        description = "Show preview of projection")

    use_projection_outline: BoolProperty(
        name = "Outline", default = True,
        description = "Show projection outline")

    use_normal_highlight: BoolProperty(
        name = "Normal Highlight", default = False,
        description = "Show stretching factor")

    # Current image preview
    use_current_image_preview: BoolProperty(
        name = "Current image", default = True,
        description = "Display currently used source image directly in the viewport")

    current_image_size: IntProperty(
        name = "Scale",
        default = 250, min = 100, soft_max = 1500,
        subtype = 'PIXEL',
        description = "Scale of displayed image in pixels")

    current_image_alpha: FloatProperty(
        name = "Alpha",
        default = 0.25, soft_min = 0.0, soft_max = 1.0, step = 1,
        subtype = 'FACTOR',
        description = "Alpha value for image")

    current_image_position: FloatVectorProperty(
        name = "Pos", size = 2,
        default = (0.0, 0.0), min = 0.0, max = 1.0)

    # Warnings
    use_warnings: BoolProperty(
        name = "Use warnings", default = False,
        description = "Show warning when paint may become laggy")

    use_warning_action_draw: BoolProperty(
        name = "Brush Preview", default = True,
        description = "Change brush preview when context out of"
                      "recommended parameters")

    use_warning_action_popup: BoolProperty(
        name = "Info popup", default = False,
        description = "Info popup when context out of recommended parameters")

    use_warning_action_lock: BoolProperty(
        name = "Lock Paint", default = True,
        description = "Lock paint when context out of recommended parameters")

    distance_warning: FloatProperty(
        name = "View Distance",
        default = 30.0, soft_min = 5, soft_max = 100,
        subtype = 'DISTANCE',
        description = "Safe distance to the view location")

    brush_radius_warning: IntProperty(
        name = "Brush Radius",
        default = 150, soft_min = 5, soft_max = 250,
        subtype = 'PIXEL',
        description = "Safe brush radius")

    canvas_size_warning: IntProperty(
        name = "Canvas Size",
        default = 4096, soft_min = 5, soft_max = 100, step = 10,
        subtype = 'PIXEL',
        description = "Safe canvas image resolution")


class ImageProperties(PropertyGroup):
    @property
    def static_size(self):
        image = self.id_data
        if image.packed_file:
            data = image.packed_file.data
            size = image.packed_file.size
            with io.BytesIO(data) as io_bytes:
                image_metadata_size = utils_image.get_image_metadata_from_bytesio(io_bytes, size)
        else:
            file_path = bpy.path.abspath(image.filepath)
            size = os.path.getsize(file_path)
            with io.open(file_path, "rb") as io_bytes:
                image_metadata_size = utils_image.get_image_metadata_from_bytesio(io_bytes, size)

        return image_metadata_size


classes = [
    CameraProperties,
    SceneProperties,
    ImageProperties
]

_register, _unregister = bpy.utils.register_classes_factory(classes)


def register():
    _register()

    bpy.types.Camera.cpp = PointerProperty(type = CameraProperties)
    bpy.types.Scene.cpp = PointerProperty(type = SceneProperties)
    bpy.types.Image.cpp = PointerProperty(type = ImageProperties)


def unregister():
    _unregister()

    del bpy.types.Camera.cpp
    del bpy.types.Scene.cpp
    del bpy.types.Image.cpp
