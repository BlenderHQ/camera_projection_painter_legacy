from bpy.types import Menu

from ..icons import get_icon_id
from ..utils import utils_state
from ..operators import CPP_OT_bind_camera_image, CPP_OT_set_camera_active


class CPP_MT_camera_pie(Menu):
    bl_label = "Camera Paint"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()
        pie.emboss = 'RADIAL_MENU'
        col = pie.column()
        col.emboss = 'RADIAL_MENU'

        cam = utils_state.state.tmp_camera
        col.label(text = "Camera: %s" % cam.name)
        col.emboss = 'NORMAL'
        col = col.column(align = True)

        if cam.data.cpp.image:
            scol = col.column()
            scol.emboss = 'NONE'
            scol.prop(cam.data.cpp, "used")
            col.template_ID_preview(cam.data.cpp, "image", open = "image.open", rows = 3, cols = 8)
        else:
            scol = col.column()
            scol.emboss = 'NONE'
            scol.prop(cam.data.cpp, "used")
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
