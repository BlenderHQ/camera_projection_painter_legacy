import bpy
import gpu
from bpy.types import SpaceView3D

from .utils_draw import draw_projection_preview
from ..constants import TEMP_DATA_NAME, TIME_STEP

import time


class PropertyTracker(object):
    __slots__ = ("value",)

    def __init__(self, value = None):
        self.value = value

    def __call__(self, value = None):
        if self.value != value:
            self.value = value
            return True
        return False


class CameraProjectionPainterBaseUtils:
    clone_image: bpy.types.Image
    camera: bpy.types.Object
    image_batch: gpu.types.GPUBatch
    mesh_batch: gpu.types.GPUBatch
    suspended: bool
    draw_handler: object
    setup_required: bool
    brush_texture_bindcode: int

    check_brush_curve_updated: PropertyTracker

    def set_properties_defaults(self):
        self.suspended = False
        self.mesh_batch = None
        self.image_batch = None
        self.draw_handler = None
        self.setup_required = True
        self.brush_texture_bindcode = 0

        self.camera = None
        self.clone_image = None

        self.check_brush_curve_updated = PropertyTracker()

    def register_modal(self, context):
        wm = context.window_manager
        wm.event_timer_add(time_step = TIME_STEP, window = context.window)
        wm.modal_handler_add(self)

    def add_draw_handlers(self, context):
        args = (self, context)
        callback = draw_projection_preview
        self.draw_handler = SpaceView3D.draw_handler_add(callback, args, 'WINDOW', 'PRE_VIEW')

    def remove_draw_handlers(self):
        if self.draw_handler:
            SpaceView3D.draw_handler_remove(self.draw_handler, 'WINDOW')

    @staticmethod
    def set_clone_image_from_camera_data(context):
        scene = context.scene
        camera = scene.camera.data
        image_paint = scene.tool_settings.image_paint
        if camera.cpp.available:
            image = camera.cpp.image
            if image:
                image_paint.clone_image = image

    @staticmethod
    def setup_basis_uv_layer(context):
        scene = context.scene
        image_paint = scene.tool_settings.image_paint
        clone_image = image_paint.clone_image
        ob = context.image_paint_object
        uv_layers = ob.data.uv_layers

        dt = time.time()  # DEBUG #######################################################

        if TEMP_DATA_NAME not in uv_layers:
            uv_layers.new(name = TEMP_DATA_NAME, do_init = False)
            uv_layer = uv_layers[TEMP_DATA_NAME]
            uv_layer.active = False
            uv_layer.active_clone = True

        if TEMP_DATA_NAME not in ob.modifiers:
            bpy.ops.object.modifier_add(type = 'UV_PROJECT')
            modifier = ob.modifiers[-1]
            modifier.name = TEMP_DATA_NAME

        modifier = ob.modifiers[TEMP_DATA_NAME]
        uv_layer = uv_layers[TEMP_DATA_NAME]

        while ob.modifiers[0] != modifier:  # Required when object already has some modifiers on it
            bpy.ops.object.modifier_move_up(modifier = modifier.name)

        modifier.uv_layer = uv_layer.name

        modifier.scale_x = 1.0
        modifier.scale_y = 1.0

        size_x, size_y = clone_image.size

        print(time.time() - dt)  # DEBUG #######################################################
        if size_x > size_y:
            modifier.aspect_x = size_x / size_y
            modifier.aspect_y = 1.0
        elif size_y > size_x:
            modifier.aspect_x = 1.0
            modifier.aspect_y = size_x / size_y
        else:
            modifier.aspect_x = 1.0
            modifier.aspect_y = 1.0

        modifier.projector_count = 1
        modifier.projectors[0].object = scene.camera

        # Scene resolution for background images
        # TODO: Remove next 3 lines
        scene.render.resolution_x = size_x
        scene.render.resolution_y = size_y
        clone_image.colorspace_settings.name = 'Raw'

    @staticmethod
    def remove_uv_layer(context):
        ob = context.active_object
        if not ob:
            if ob.type == 'MESH':
                uv_layers = ob.data.uv_layers
                if TEMP_DATA_NAME in uv_layers:
                    uv_layers.remove(uv_layers[TEMP_DATA_NAME])

    @staticmethod
    def remove_modifier(context):
        ob = context.active_object
        if ob:
            if ob.type == 'MESH':
                if TEMP_DATA_NAME in ob.modifiers:
                    bpy.ops.object.modifier_remove(modifier = TEMP_DATA_NAME)
