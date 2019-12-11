from ..constants import TEMP_DATA_NAME


def _check_uv_layers(ob):
    uv_layers = ob.data.uv_layers
    uv_layers_count = len(uv_layers)
    if TEMP_DATA_NAME in uv_layers:
        uv_layers_count -= 1

    if uv_layers_count and uv_layers.active.name != TEMP_DATA_NAME:
        return True
    return False


def tool_setup_poll(context):
    tool = context.workspace.tools.from_space_view3d_mode(context.mode, create = False)

    if not tool:
        return False
    if tool.idname != "builtin_brush.Clone":
        return False

    scene = context.scene
    image_paint = scene.tool_settings.image_paint

    if image_paint.mode != 'IMAGE':
        return False
    if not image_paint.use_clone_layer:
        return False
    cpp = getattr(scene, "cpp", None)
    if not cpp:
        return False
    if scene.cpp.mapping != 'CAMERA':
        return False

    ob = context.image_paint_object
    if not _check_uv_layers(ob):
        return False

    return True


def full_poll(context):
    if not tool_setup_poll(context):
        return False

    scene = context.scene
    if not scene.camera:
        return False

    image_paint = scene.tool_settings.image_paint
    if not image_paint.detect_data():
        return False
    if not image_paint.clone_image:
        return False

    return True