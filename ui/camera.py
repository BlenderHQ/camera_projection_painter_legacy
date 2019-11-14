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
        layout.use_property_decorate = False

        data = context.object.data

        col = layout.column(align = True)
        col.enabled = data.cpp.used

        image = data.cpp.image
        if image:
            col.template_ID_preview(data.cpp, "image", open = "image.open", rows = 3, cols = 8)
        else:
            col.template_ID(data.cpp, "image", open = "image.open")

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


class CPP_PT_cpp_camera_calibration(Panel):
    bl_label = "Calibration"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_parent_id = "CPP_PT_cpp_camera_options"

    @classmethod
    def poll(cls, context):
        data = context.object.data
        image = data.cpp.image
        return True if image else False

    def draw_header(self, context):
        layout = self.layout
        data = context.object.data
        layout.prop(data.cpp, "use_calibration", text = "")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(align = True)

        data = context.object.data

        col.enabled = data.cpp.use_calibration

        col.prop(data.cpp, "calibration_principal_point")
        col.separator()
        col.prop(data.cpp, "calibration_skew")
        col.prop(data.cpp, "calibration_aspect_ratio")
        col.prop(data.cpp, "lens_distortion_radial_1")
        col.prop(data.cpp, "lens_distortion_radial_2")
        col.prop(data.cpp, "lens_distortion_radial_3")
        col.prop(data.cpp, "lens_distortion_tangential_1")
        col.prop(data.cpp, "lens_distortion_tangential_2")
