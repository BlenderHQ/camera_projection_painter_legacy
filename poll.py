# <pep8 compliant>

# The module contains basic methods for checking context for compatible conditions

import importlib
import os

import bpy

from . import constants

if "_rc" in locals():  # In case of module reloading
    importlib.reload(constants)

_rc = None


def check_uv_layers(ob: bpy.types.Object):
    """
    Positive if there is at least one layer and TEMP_DATA_NAME layer is not active
    """
    if ob and ob.type == 'MESH':
        uv_layers = ob.data.uv_layers
        uv_layers_count = len(uv_layers)

        if constants.TEMP_DATA_NAME in uv_layers:
            uv_layers_count -= 1

        if uv_layers_count and uv_layers.active.name != constants.TEMP_DATA_NAME:
            return True
    return False


def tool_setup_poll(context: bpy.types.Context):
    """
    The conditions under which the gizmo is available appears under the scene settings panel in the toolbar
    """
    tool = context.workspace.tools.from_space_view3d_mode(
        context.mode, create=False)

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

    if scene.cpp.mapping != 'CAMERA':
        return False

    ob = context.image_paint_object
    if not check_uv_layers(ob):
        return False

    return True


def full_poll(context: bpy.types.Context):
    """
    Conditions under which the start of the main operator
    """
    if not tool_setup_poll(context):
        return False

    scene = context.scene
    image_paint = scene.tool_settings.image_paint

    canvas = image_paint.canvas
    if not canvas:
        return False
    if canvas.source == 'TILED':  # Blender version 2.82a
        file_path = canvas.filepath
        if not file_path:
            return False
        elif not os.path.isfile(bpy.path.abspath(file_path)):
            return False
    if not canvas.cpp.valid:
        return False


    if not scene.camera:
        return False
    if not image_paint.detect_data():
        return False
    if not image_paint.clone_image:
        return False

    return True
