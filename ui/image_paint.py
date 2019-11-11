import bpy
from bpy.types import Panel

from ..icons import get_icon_id
from ..operators import CPP_OT_bind_camera_image, CPP_OT_set_camera_by_view
from ..utils import utils_poll


class CPPOptionsPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Camera Paint"
    bl_category = "Camera Paint"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return utils_poll.tool_setup_poll(context)


class CPP_PT_options(Panel, CPPOptionsPanel):
    bl_label = "Camera Paint"
    bl_options = set()

    def draw(self, context):
        pass  # Just a container


class CPP_PT_scene_options(Panel, CPPOptionsPanel):
    bl_label = "Scene"
    bl_parent_id = "CPP_PT_options"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(align = False)

        scene = context.scene

        col.label(text = "Source Images Directory:")
        col.prop(scene.cpp, "source_images_path", text = "", icon = 'IMAGE')
        scol = col.column()
        scol.enabled = scene.cpp.has_visible_camera_objects
        operator = scol.operator(
            CPP_OT_bind_camera_image.bl_idname,
            text = "Bind All",
            icon_value = get_icon_id("bind_image"))
        operator.mode = 'ALL'


class CPP_PT_camera_options(bpy.types.Panel, CPPOptionsPanel):
    bl_label = "Cameras"
    bl_parent_id = "CPP_PT_options"
    bl_options = set()

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align = False)
        scene = context.scene
        col.prop(scene.cpp, "cameras_viewport_size")


class CPP_PT_camera_background_images_options(Panel, CPPOptionsPanel):
    bl_label = "Background Images"
    bl_parent_id = "CPP_PT_camera_options"

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene.cpp, "use_background_images", text = "")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(align = False)

        scene = context.scene
        col.enabled = scene.cpp.use_background_images
        col.prop(scene.cpp, "background_images_alpha")


class CPP_PT_camera_autocam_options(Panel, CPPOptionsPanel):
    bl_label = "Autocam"
    bl_parent_id = "CPP_PT_camera_options"

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene.cpp, "use_auto_set_camera", text = "")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(align = False)

        scene = context.scene

        scol = col.column()
        scol.enabled = not scene.cpp.use_auto_set_camera
        scol.operator(CPP_OT_set_camera_by_view.bl_idname, icon = 'VIEW_CAMERA')

        col.label(text = "Options:")

        row = col.row(align = True)
        row.use_property_split = False
        row.prop_enum(scene.cpp, "auto_set_camera_method", 'FULL')
        row.prop_enum(scene.cpp, "auto_set_camera_method", 'DIRECTION')
        method = scene.cpp.auto_set_camera_method
        if method == 'FULL':
            col.prop(scene.cpp, "tolerance_full")
        elif method == 'DIRECTION':
            col.prop(scene.cpp, "tolerance_direction")


class CPP_PT_view_options(Panel, CPPOptionsPanel):
    bl_label = "View"
    bl_parent_id = "CPP_PT_options"
    bl_options = set()

    def draw(self, context):
        pass


class CPP_PT_view_projection_preview_options(Panel, CPPOptionsPanel):
    bl_label = "Projection Preview"
    bl_parent_id = "CPP_PT_view_options"

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene.cpp, "use_projection_preview", text = "")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(align = False)

        scene = context.scene
        col.enabled = scene.cpp.use_projection_preview
        col.prop(scene.cpp, "use_normal_highlight")
        col.prop(scene.cpp, "use_projection_outline")


class CPP_PT_current_image_preview_options(Panel, CPPOptionsPanel):
    bl_label = "Current Image"
    bl_parent_id = "CPP_PT_view_options"

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene.cpp, "use_current_image_preview", text = "")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(align = False)

        scene = context.scene

        col.enabled = scene.cpp.use_current_image_preview
        col.prop(scene.cpp, "current_image_alpha")
        col.prop(scene.cpp, "current_image_size")


class CPP_PT_current_warnings_options(Panel, CPPOptionsPanel):
    bl_label = "Warnings"
    bl_parent_id = "CPP_PT_view_options"

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene.cpp, "use_warnings", text = "")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(align = False)

        scene = context.scene

        col.enabled = scene.cpp.use_warnings
        col.prop(scene.cpp, "distance_warning")
        col.prop(scene.cpp, "brush_radius_warning")
        col.prop(scene.cpp, "canvas_size_warning")
