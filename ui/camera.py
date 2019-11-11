from bpy.types import Panel

from ..icons import get_icon_id
from ..utils.utils_state import state
from ..operators import CPP_OT_bind_camera_image


class CPP_PT_cpp_camera_options(Panel):
    bl_label = "Camera Paint"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if not state.operator:
            return False
        return context.active_object.type == 'CAMERA'

    def draw_header(self, context):
        layout = self.layout
        data = context.object.data
        layout.prop(data.cpp, "used", text = "", text_ctxt = "CPP")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        data = context.object.data

        col = layout.column(align = True)
        col.enabled = data.cpp.used

        if data.cpp.image:
            col.template_ID_preview(data.cpp, "image", open = "image.open", rows = 3, cols = 8)
        else:
            col.template_ID(data.cpp, "image", open = "image.open")

        operator = col.operator(CPP_OT_bind_camera_image.bl_idname, icon_value = get_icon_id("bind_image"))
        operator.mode = 'ACTIVE'