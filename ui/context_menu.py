from bpy.types import Menu

from ..icons import get_icon_id

from ..operators import CPP_OT_bind_camera_image, CPP_OT_set_camera_active
from .. import operators


class CPP_MT_camera_pie(Menu):
    bl_label = "Camera Paint"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.emboss = 'RADIAL_MENU'
        col = pie.column()
        col.emboss = 'RADIAL_MENU'

        cam = operators.tmp_camera
        if cam:
            col.label(text = "Camera:")
            col.label(text = cam.name)
            col.emboss = 'NORMAL'
            col = col.column(align = True)

            scol = col.column()
            scol.emboss = 'NONE'
            scol.prop(cam.data.cpp, "used")
            if cam.data.cpp.image:
                col.template_ID_preview(cam.data.cpp, "image", open = "image.open", rows = 3, cols = 8)
            else:
                col.template_ID(cam.data.cpp, "image")

            operator = pie.operator(CPP_OT_bind_camera_image.bl_idname, icon_value = get_icon_id("bind_image"))
            operator.mode = 'TMP'

            col = pie.column()
            col.emboss = 'NONE'
            col.separator()

            text = None
            if context.scene.camera == cam:
                text = "Already active"
            pie.operator(CPP_OT_set_camera_active.bl_idname, text = text, icon_value = get_icon_id("set_active"))
