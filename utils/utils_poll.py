import bpy

from .utils_state import state
from ..constants import TEMP_DATA_NAME


def base_poll(context):
    if not state.operator:
        return False
    ob = context.image_paint_object
    camera = context.scene.camera
    if ob and camera:
        return True
    return False


def tool_setup_poll(context):
    if not base_poll(context):
        return False
    scene = context.scene
    tool = context.workspace.tools.from_space_view3d_mode(context.mode, create = False)
    image_paint = scene.tool_settings.image_paint
    ob = context.image_paint_object

    uv_layers = ob.data.uv_layers
    uv_layers_count = len(uv_layers)
    if TEMP_DATA_NAME in uv_layers:
        uv_layers_count -= 1

        if uv_layers.active.name == TEMP_DATA_NAME:
            return False

    if not uv_layers_count:
        return False

    if tool.idname == "builtin_brush.Clone":
        if image_paint.mode == 'IMAGE' and image_paint.use_clone_layer:
            if scene.cpp.mapping == 'CAMERA':
                return True
    return False


def full_poll(context):
    if tool_setup_poll(context):
        scene = context.scene
        image_paint = scene.tool_settings.image_paint
        if image_paint.clone_image:
            return True
    return False


def full_poll_decorator(func):
    def wrapper(*args):
        context = [n for n in args if type(n) == bpy.types.Context][0]
        if full_poll(context):
            return func(*args)

    return wrapper
