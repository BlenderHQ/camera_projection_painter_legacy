# <pep8 compliant>

# The module contains class methods that are used not only in one place

import importlib

from .. import operators
from .. import icons

if "_rc" in locals(): # In case of module reloading
    importlib.reload(operators)
    importlib.reload(icons)

_rc = None


def camera_image(layout, camera_ob, mode = 'CONTEXT'):
    layout.use_property_split = True
    layout.use_property_decorate = False

    camera = camera_ob.data

    col = layout.column(align = True)

    if mode == 'TMP':
        col.ui_units_x = 11

    image = camera.cpp.image

    if image:
        col.template_ID_preview(camera.cpp, "image", open = "image.open", rows = 3, cols = 8)
    else:
        col.template_ID(camera.cpp, "image", open = "image.open")

    col.label(text = "Binding Palette:")

    row = col.row(align = False)

    row.template_list(
        "DATA_UL_bind_history_item", "",
        camera_ob.data, "cpp_bind_history",
        camera_ob.data.cpp, "active_bind_index",
        rows = 1)

    if mode in ('CONTEXT', 'TMP', 'ACTIVE'):
        row.operator(
            operator = operators.CPP_OT_bind_history_remove.bl_idname,
            text = "", icon = "REMOVE"
        ).mode = mode

    col.separator()

    if mode == 'CONTEXT':
        operator = col.operator(
            operator = operators.CPP_OT_bind_camera_image.bl_idname,
            icon_value = icons.get_icon_id("bind_image"))
        operator.mode = mode

    if image and image.cpp.valid:
        width, height = image.cpp.static_size
        depth = image.depth
        colorspace = image.colorspace_settings.name
        row = col.row()
        if mode == 'CONTEXT':
            row.label(text = "Width:")
            row.label(text = "%d px" % width)

            row = col.row()
            row.label(text = "Height:")
            row.label(text = "%d px" % height)

            row = col.row()
            row.label(text = "Pixel Format:")
            row.label(text = "%d-bit %s" % (depth, colorspace))
        # else:
        # row.label(text = "%dx%d %d-bit %s" % (width, height, depth, colorspace))

    else:
        col.label(text = "Invalid image", icon = 'ERROR')


def path_with_ops(layout, scene):
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
        icon_value = icons.get_icon_id("bind_image"))
    operator.mode = 'ALL'

    col.separator()
