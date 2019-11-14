import bpy
from bpy.types import SpaceView3D

from .utils_draw import draw_projection_preview
from ..constants import TEMP_DATA_NAME


def set_draw_handlers(self, context, state):
    if state:
        args = (self, context)
        callback = draw_projection_preview
        handler3d = SpaceView3D.draw_handler_add(callback, args, 'WINDOW', 'PRE_VIEW')
        self.draw_handler = handler3d
    else:
        if self.draw_handler:
            SpaceView3D.draw_handler_remove(self.draw_handler, 'WINDOW')
        self.draw_handler = None


def cleanup(self, context):
    if self.cleanup_required:
        self.cleanup_required = False

        set_draw_handlers(self, context, state = False)
        set_modifier(context.active_object, state = False)

        self.mesh_batch = None


def auto_set_image(context):
    scene = context.scene
    camera = scene.camera.data
    image_paint = scene.tool_settings.image_paint
    if camera.cpp.available:
        image = camera.cpp.image
        if image:
            if image_paint.clone_image != image:
                image_paint.clone_image = image


def _set_uv_layer(ob, state = True):
    uv_layers = ob.data.uv_layers
    if state:
        if TEMP_DATA_NAME not in uv_layers:
            uv_layers.new(name = TEMP_DATA_NAME, do_init = False)
            uv_layer = uv_layers[TEMP_DATA_NAME]
            uv_layer.active = False
            uv_layer.active_clone = True
        return uv_layers[TEMP_DATA_NAME]
    else:
        if TEMP_DATA_NAME in uv_layers:
            uv_layers.remove(uv_layers[TEMP_DATA_NAME])


def set_modifier(ob, state = True):
    if state:
        if TEMP_DATA_NAME not in ob.modifiers:
            bpy.ops.object.modifier_add(type = 'UV_PROJECT')
            ob.modifiers[-1].name = TEMP_DATA_NAME
            modifier = ob.modifiers[TEMP_DATA_NAME]
            uv_layer = _set_uv_layer(ob, True)
            modifier.uv_layer = uv_layer.name
            modifier.projector_count = 1
            modifier.scale_x = 1.0
            modifier.scale_y = 1.0
        modifier = ob.modifiers[TEMP_DATA_NAME]
        if ob.modifiers[-1] != modifier:
            while ob.modifiers[-1] != modifier:
                bpy.ops.object.modifier_move_down(modifier = TEMP_DATA_NAME)
        return ob.modifiers[TEMP_DATA_NAME]
    else:
        if TEMP_DATA_NAME in ob.modifiers:
            bpy.ops.object.modifier_remove(modifier = TEMP_DATA_NAME)
        _set_uv_layer(ob, False)
