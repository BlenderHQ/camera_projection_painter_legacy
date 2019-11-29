from bpy.types import Panel

from .templates import template_path

from ..icons import get_icon_id
from ..utils.utils_state import state
from ..operators import CPP_OT_bind_camera_image, CPP_OT_set_camera_calibration_from_file, CPP_OT_enter_context


class SceneButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if not state.operator:
            return False
        return True


class CPP_PT_camera_projection_painter(Panel, SceneButtonsPanel):
    bl_label = "Camera Paint"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align = True)
        col.operator(CPP_OT_enter_context.bl_idname, icon_value = get_icon_id("run"))


class CPP_PT_path(Panel, SceneButtonsPanel):
    bl_label = "Path"
    bl_parent_id = "CPP_PT_camera_projection_painter"
    bl_options = set()  # default opened

    def draw(self, context):
        layout = self.layout
        template_path(layout, context.scene)


class CPP_PT_scene_cameras(Panel, SceneButtonsPanel):
    bl_label = "Cameras"
    bl_parent_id = "CPP_PT_camera_projection_painter"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align = True)

        scene = context.scene

        scol = col.column()
        scol.enabled = scene.cpp.has_camera_objects_selected
        operator = scol.operator(
            CPP_OT_bind_camera_image.bl_idname,
            text = "Bind Selected Camera Images",
            text_ctxt = "CPP",
            icon_value = get_icon_id("bind_image"))
        operator.mode = 'SELECTED'

        scol = col.column()
        scol.enabled = scene.cpp.has_camera_objects
        operator = scol.operator(
            CPP_OT_bind_camera_image.bl_idname,
            text = "Bind All Camera Images",
            text_ctxt = "CPP",
            icon_value = get_icon_id("bind_image"))
        operator.mode = 'ALL'

        scol = col.column()
        # scol.operator(CPP_OT_set_camera_calibration_from_file.bl_idname,
        #              icon_value = get_icon_id("calibration"))
