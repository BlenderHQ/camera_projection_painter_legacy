import bpy
from bpy.types import Panel

from .templates import (
    template_camera_image,
    template_camera_calibration,
    template_camera_lens_distortion)

from ..operators import CPP_OT_set_camera_by_view, CPP_OT_free_memory
from ..utils import utils_poll, utils_draw


class CPPOptionsPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Camera Paint"
    bl_category = "Camera Paint"
    bl_options = {'DEFAULT_CLOSED'}


class CPP_PT_camera_painter(Panel, CPPOptionsPanel):
    bl_label = "Camera Paint"
    bl_options = set()

    @classmethod
    def poll(cls, context):
        return utils_poll.tool_setup_poll(context)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align = False)
        scene = context.scene

        if not scene.camera:
            col.label(text = "Scene has no camera", icon = 'ERROR')
        image_paint = scene.tool_settings.image_paint
        if not image_paint.canvas:
            col.label(text = "Brush has no canvas", icon = 'ERROR')
        if not image_paint.clone_image:
            col.label(text = "Brush has no clone image", icon = 'ERROR')


# View Options
class CPP_PT_view_options(Panel, CPPOptionsPanel):
    bl_label = "View"
    bl_parent_id = "CPP_PT_camera_painter"
    bl_options = set()
    bl_order = 0

    @classmethod
    def poll(cls, context):
        return utils_poll.full_poll(context)

    def draw(self, context):
        pass


class CPP_PT_camera_options(bpy.types.Panel, CPPOptionsPanel):
    bl_label = "Cameras"
    bl_parent_id = "CPP_PT_view_options"
    bl_options = set()
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align = False)
        scene = context.scene

        col.use_property_split = False
        col.prop(scene.cpp, "cameras_viewport_size")
        col.use_property_split = True

        ready_count = utils_draw.get_ready_preview_count()
        valid_count = len([n for n in bpy.data.images if not n.cpp.invalid])

        text = "Image previews:"
        if ready_count < valid_count:
            text = "Image previews (%d/%d ready):" % (ready_count, valid_count)

        col.label(text = text)

        col.operator("wm.previews_ensure", icon = 'FREEZE')
        col.prop(scene.cpp, "use_camera_image_previews")


class CPP_PT_view_projection_options(Panel, CPPOptionsPanel):
    bl_label = "Projection"
    bl_parent_id = "CPP_PT_view_options"
    bl_order = 1

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
        col.prop(scene.cpp, "use_warning_action_draw")


class CPP_PT_current_image_preview_options(Panel, CPPOptionsPanel):
    bl_label = "Current Image"
    bl_parent_id = "CPP_PT_view_options"
    bl_order = 2

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene.cpp, "use_current_image_preview", text = "")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False
        col = layout.column(align = False)

        scene = context.scene

        col.enabled = scene.cpp.use_current_image_preview
        col.prop(scene.cpp, "current_image_alpha")
        col.prop(scene.cpp, "current_image_size")


# Utils
class CPP_PT_operator_options(Panel, CPPOptionsPanel):
    bl_label = "Options"
    bl_parent_id = "CPP_PT_camera_painter"
    bl_options = set()
    bl_order = 1

    @classmethod
    def poll(cls, context):
        return utils_poll.full_poll(context)

    def draw(self, context):
        pass


class CPP_PT_camera_autocam_options(Panel, CPPOptionsPanel):
    bl_label = "Autocam"
    bl_parent_id = "CPP_PT_operator_options"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        return utils_poll.full_poll(context)

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene.cpp, "use_auto_set_camera", text = "")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False
        col = layout.column(align = False)

        scene = context.scene

        scol = col.column()
        scol.enabled = not scene.cpp.use_auto_set_camera
        scol.operator(CPP_OT_set_camera_by_view.bl_idname)

        col.label(text = "Options:")

        row = col.row(align = True)
        row.prop_enum(scene.cpp, "auto_set_camera_method", 'FULL')
        row.prop_enum(scene.cpp, "auto_set_camera_method", 'DIRECTION')
        method = scene.cpp.auto_set_camera_method

        if method == 'FULL':
            col.prop(scene.cpp, "tolerance_full")
        elif method == 'DIRECTION':
            col.prop(scene.cpp, "tolerance_direction")


class CPP_PT_warnings_options(Panel, CPPOptionsPanel):
    bl_label = "Warnings"
    bl_parent_id = "CPP_PT_operator_options"
    bl_order = 3

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene.cpp, "use_warnings", text = "")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False
        col = layout.column(align = True)

        scene = context.scene

        col.enabled = scene.cpp.use_warnings

        col.prop(scene.cpp, "distance_warning")
        col.prop(scene.cpp, "brush_radius_warning")
        col.prop(scene.cpp, "canvas_size_warning")

        col.label(text = "Actions:")
        col.use_property_split = True

        col.prop(scene.cpp, "use_warning_action_popup")
        col.prop(scene.cpp, "use_warning_action_lock")


class CPP_PT_memory_options(Panel, CPPOptionsPanel):
    bl_label = "Memory Management"
    bl_parent_id = "CPP_PT_warnings_options"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False
        col = layout.column(align = False)

        row = col.row()
        row.label(text = "Images loaded:")
        row.label(text = "%d" % utils_draw.get_loaded_images_count())

        col.operator(CPP_OT_free_memory.bl_idname)


class CPP_PT_current_camera(Panel, CPPOptionsPanel):
    bl_label = "Current Camera"
    bl_parent_id = "CPP_PT_operator_options"
    bl_options = set()
    bl_order = 0

    @classmethod
    def poll(cls, context):
        scene = context.scene
        camera_ob = context.scene.camera
        if not camera_ob:
            return False
        if camera_ob.type != 'CAMERA':
            return False
        return utils_poll.tool_setup_poll(context) and scene.camera

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False
        col = layout.column(align = False)

        camera_ob = context.scene.camera

        template_camera_image(col, camera_ob)


class CPP_PT_current_camera_calibration(Panel, CPPOptionsPanel):
    bl_label = "Calibration"
    bl_parent_id = "CPP_PT_current_camera"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        data = scene.camera.data.cpp
        image = data.image
        return True if image else False

    def draw_header(self, context):
        layout = self.layout
        scene = context.scene
        data = scene.camera.data.cpp
        layout.prop(data, "use_calibration", text = "")

    def draw(self, context):
        layout = self.layout
        template_camera_calibration(layout, context.scene.camera)


class CPP_PT_current_camera_lens_distortion(Panel, CPPOptionsPanel):
    bl_label = "Lens Distortion"
    bl_parent_id = "CPP_PT_current_camera_calibration"

    def draw(self, context):
        layout = self.layout
        template_camera_lens_distortion(layout, context.scene.camera)
