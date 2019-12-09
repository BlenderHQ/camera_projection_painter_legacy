import bpy

from ..constants import TEMP_DATA_NAME


def full_poll(context):
    scene = context.scene
    image_paint = scene.tool_settings.image_paint
    if scene.camera and image_paint.detect_data():
        tool = context.workspace.tools.from_space_view3d_mode(context.mode, create = False)
        if tool.idname == "builtin_brush.Clone":
            if (image_paint.mode == 'IMAGE'
                    and image_paint.use_clone_layer
                    and scene.cpp.mapping == 'CAMERA'
                    and image_paint.clone_image):

                ob = context.image_paint_object
                uv_layers = ob.data.uv_layers
                uv_layers_count = len(uv_layers)
                if TEMP_DATA_NAME in uv_layers:
                    uv_layers_count -= 1

                if uv_layers_count and uv_layers.active.name != TEMP_DATA_NAME:
                    return True
    return False


def full_poll_decorator(func):
    def wrapper(*args):
        context = [n for n in args if type(n) == bpy.types.Context][0]
        if full_poll(context):
            return func(*args)

    return wrapper
