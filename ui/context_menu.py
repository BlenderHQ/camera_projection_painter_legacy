from bpy.types import Menu

from .. import operators
from ..operators import CPP_OT_bind_camera_image, CPP_OT_set_camera_active
from ..icons import get_icon_id


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

            scol = col.column()
            scol.emboss = 'NONE'

            if camera_ob.data.cpp.image:
                col.template_ID_preview(camera_ob.data.cpp, "image", open = "image.open", rows = 3, cols = 8)
            else:
                col.template_ID(camera_ob.data.cpp, "image")

            operator = pie.operator(CPP_OT_bind_camera_image.bl_idname, icon_value = get_icon_id("bind_image"))
            operator.mode = 'TMP'

            col = pie.column()
            col.emboss = 'NONE'
            col.separator()

            text = None
            if scene.cpp.use_auto_set_camera:
                text = "Automatic Selection Used"
            if scene.camera == camera_ob:
                text = "Already active"
            pie.operator(CPP_OT_set_camera_active.bl_idname, text = text, icon_value = get_icon_id("set_active"))
