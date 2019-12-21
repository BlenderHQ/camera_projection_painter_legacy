# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(operators)
    importlib.reload(icons)

    del importlib
else:
    from .. import operators
    from .. import icons

import bpy

from .. import operators
from .. import icons


class CPP_PT_camera_painter_scene(bpy.types.Panel):
    bl_label = "Camera Paint"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align = True)

        scene = context.scene

        col.prop(scene.cpp, "source_images_path", icon = 'IMAGE')
        # col.prop(scene.cpp, "calibration_source_file", icon = 'FILE_CACHE')

        col.separator()

        col.operator(
            operator = operators.CPP_OT_enter_context.bl_idname,
            icon_value = icons.get_icon_id("run")
        )

        scol = col.column()
        scol.enabled = scene.cpp.has_camera_objects_selected
        operator = scol.operator(
            operator = operators.CPP_OT_bind_camera_image.bl_idname,
            text = "Bind Selected Camera Images",
            text_ctxt = "CPP",
            icon_value = icons.get_icon_id("bind_image"))
        operator.mode = 'SELECTED'

        scol = col.column()
        scol.enabled = scene.cpp.has_camera_objects
        operator = scol.operator(
            operator = operators.CPP_OT_bind_camera_image.bl_idname,
            text = "Bind All Camera Images",
            text_ctxt = "CPP",
            icon_value = icons.get_icon_id("bind_image"))
        operator.mode = 'ALL'

        # scol = col.column()
        # scol.operator(
        #              operator = CPP_OT_set_camera_calibration_from_file.bl_idname,
        #              icon_value = get_icon_id("calibration"))
