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

from .. import operators
from ..icons import get_icon_id


def template_camera_image(layout, camera_ob):
    layout.use_property_split = True
    layout.use_property_decorate = False

    camera = camera_ob.data

    col = layout.column(align = True)

    image = camera.cpp.image
    if image:
        col.template_ID_preview(camera.cpp, "image", open = "image.open", rows = 3, cols = 8)
    else:
        col.template_ID(camera.cpp, "image", open = "image.open")

    operator = col.operator(
        operator = operators.CPP_OT_bind_camera_image.bl_idname,
        icon_value = get_icon_id("bind_image"))
    operator.mode = 'ACTIVE'

    if image:

        if not image.cpp.invalid:
            size_x, size_y = image.cpp.static_size
            row = col.row()
            row.label(text = "Width:")
            row.label(text = "%d px" % size_x)

            row = col.row()
            row.label(text = "Height:")
            row.label(text = "%d px" % size_y)

            row = col.row()
            row.label(text = "Pixel Format:")
            row.label(text = "%d-bit %s" % (image.depth, image.colorspace_settings.name))
        else:
            col.label(text = "Invalid image", icon = 'ERROR')


def template_camera_calibration(layout, camera_ob):
    layout.use_property_decorate = False

    col = layout.column(align = True)

    data = camera_ob.data

    col.enabled = data.cpp.use_calibration

    col.use_property_split = True
    col.prop(data, "lens")
    col.separator()
    layout.use_property_split = False
    col.prop(data.cpp, "calibration_principal_point")
    col.separator()

    col.use_property_split = True
    col.prop(data.cpp, "calibration_skew")
    col.prop(data.cpp, "calibration_aspect_ratio")


def template_camera_lens_distortion(layout, camera_ob):
    layout.use_property_decorate = False
    layout.use_property_split = True

    col = layout.column(align = True)

    data = camera_ob.data

    col.enabled = data.cpp.use_calibration

    col.prop(data.cpp, "lens_distortion_radial_1")
    col.prop(data.cpp, "lens_distortion_radial_2")
    col.prop(data.cpp, "lens_distortion_radial_3")
    col.prop(data.cpp, "lens_distortion_tangential_1")
    col.prop(data.cpp, "lens_distortion_tangential_2")


def template_path_with_ops(layout, scene):
    layout.use_property_split = False
    layout.use_property_decorate = False
    col = layout.column(align = False)

    col.label(text = "Source Images Directory:")
    col.prop(scene.cpp, "source_images_path", text = "", icon = 'IMAGE')
    scol = col.column()
    scol.enabled = scene.cpp.has_camera_objects
    operator = scol.operator(
        operator = operators.CPP_OT_bind_camera_image,
        text = "Bind All",
        icon_value = get_icon_id("bind_image"))
    operator.mode = 'ALL'

    col.separator()

    # col.prop(scene.cpp, "calibration_source_file", text = "", icon = 'FILE_CACHE')
    # col.operator(operators.CPP_OT_set_camera_calibration_from_file.bl_idname,
    #             icon_value = get_icon_id("calibration"))
