# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(template)
    importlib.reload(operators)
    importlib.reload(icons)

    del importlib
else:
    from . import template
    from .. import operators
    from .. import icons

import bpy
from bpy.types import Menu


class CPP_MT_camera_pie(Menu):
    bl_label = "Camera Paint"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        col = pie.column(align = True)

        camera_ob = operators.tmp_camera

        if camera_ob:
            col.label(text = "Camera:")
            col.emboss = 'RADIAL_MENU'
            col.label(text = camera_ob.name)
            col.emboss = 'NORMAL'
            col = col.column(align = True)

            scene = context.scene

            template.camera_image(col, camera_ob, mode = 'TMP')

            operator = pie.operator(
                operator = operators.CPP_OT_bind_camera_image.bl_idname,
                icon_value = icons.get_icon_id("bind_image"))
            operator.mode = 'TMP'

            col = pie.column()
            col.emboss = 'NONE'
            col.separator()

            text = None
            if scene.camera == camera_ob:
                text = "Already active"
            pie.operator(
                operator = operators.CPP_OT_set_camera_active.bl_idname,
                text = text, icon_value = icons.get_icon_id("set_active"))
