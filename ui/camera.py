from bpy.types import Panel

from .templates import (
    template_camera_image,
    template_camera_calibration,
    template_camera_lens_distortion)

from .. import operators


class CameraOptionsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}


class CPP_PT_active_camera_options(Panel, CameraOptionsPanel):
    bl_label = "Camera Paint"

    @classmethod
    def poll(cls, context):
        return context.object.type == 'CAMERA'

    def draw(self, context):
        layout = self.layout

        template_camera_image(layout, context.active_object)


class CPP_PT_active_camera_calibration(Panel, CameraOptionsPanel):
    bl_label = "Calibration"
    bl_parent_id = "CPP_PT_active_camera_options"

    @classmethod
    def poll(cls, context):
        data = context.active_object.data
        image = data.cpp.image
        return True if image else False

    def draw_header(self, context):
        layout = self.layout
        data = context.active_object.data
        layout.prop(data.cpp, "use_calibration", text = "")

    def draw(self, context):
        layout = self.layout
        template_camera_calibration(layout, context.active_object)


class CPP_PT_active_camera_lens_distortion(Panel, CameraOptionsPanel):
    bl_label = "Lens Distortion"
    bl_parent_id = "CPP_PT_active_camera_calibration"

    def draw(self, context):
        layout = self.layout
        template_camera_lens_distortion(layout, context.scene.camera)
