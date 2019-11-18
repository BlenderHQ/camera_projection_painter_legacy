import bpy

from ..icons import get_icon_id
from ..operators import CPP_OT_bind_camera_image, CPP_OT_set_camera_calibration_from_file


def template_camera_image(layout, camera_ob):
    layout.use_property_split = True
    layout.use_property_decorate = False

    camera = camera_ob.data

    col = layout.column(align = True)
    col.enabled = camera.cpp.used

    image = camera.cpp.image
    if image:
        col.template_ID_preview(camera.cpp, "image", open = "image.open", rows = 3, cols = 8)
    else:
        col.template_ID(camera.cpp, "image", open = "image.open")

    operator = col.operator(CPP_OT_bind_camera_image.bl_idname, icon_value = get_icon_id("bind_image"))
    operator.mode = 'ACTIVE'

    if image:
        sx, sy = image.size
        row = col.row()
        row.label(text = "Width:")
        row.label(text = "%d px" % sx)

        row = col.row()
        row.label(text = "Height:")
        row.label(text = "%d px" % sy)

        row = col.row()
        row.label(text = "Pixel Format:")
        row.label(text = "%d-bit %s" % (image.depth, image.colorspace_settings.name))


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


def template_path(layout, scene):
    layout.use_property_split = True
    layout.use_property_decorate = False
    col = layout.column(align = True)

    col.prop(scene.cpp, "source_images_path", icon = 'IMAGE')
    col.prop(scene.cpp, "calibration_source_file", icon = 'FILE_CACHE')


def template_path_with_ops(layout, scene):
    layout.use_property_split = False
    layout.use_property_decorate = False
    col = layout.column(align = False)

    col.label(text = "Source Images Directory:")
    col.prop(scene.cpp, "source_images_path", text = "", icon = 'IMAGE')
    scol = col.column()
    scol.enabled = scene.cpp.has_visible_camera_objects
    operator = scol.operator(
        CPP_OT_bind_camera_image.bl_idname,
        text = "Bind All",
        icon_value = get_icon_id("bind_image"))
    operator.mode = 'ALL'

    col.separator()

    col.prop(scene.cpp, "calibration_source_file", text = "", icon = 'FILE_CACHE')
    col.operator(CPP_OT_set_camera_calibration_from_file.bl_idname,
                 icon_value = get_icon_id("calibration"))
