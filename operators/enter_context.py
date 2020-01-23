# <pep8 compliant>

import importlib

import bpy

from .. import poll

if "_rc" in locals():  # In case of module reloading
    importlib.reload(poll)

_rc = None


def operator_description(cls, context, properties):
    """Operator Description Method"""
    active_object = context.active_object
    scene = context.scene
    image_paint = scene.tool_settings.image_paint

    result = ""
    queue_number = 1

    if active_object.mode != 'TEXTURE_PAINT':
        result += "%s. Object mode will be changed to Texture Paint" % queue_number
        result += "\n"
        queue_number += 1

    workspace_tool = context.workspace.tools.from_space_view3d_mode(context.mode, create=False)
    if workspace_tool.idname != "builtin_brush.Clone":
        result += "%s. Tool will be set to Clone" % queue_number
        result += "\n"
        queue_number += 1

    if image_paint.mode != 'IMAGE':
        result += "%s. Image Paint Mode will be set to Single Image" % queue_number
        result += "\n"
        queue_number += 1

    if not image_paint.use_clone_layer:
        result += "%s. Image Paint will Use Clone Layer" % queue_number
        result += "\n"
        queue_number += 1

    if scene.cpp.mapping != 'CAMERA':
        result += "%s. Image Paint Mapping will be set to Camera" % queue_number
        result += "\n"
        queue_number += 1

    if not scene.cpp.use_auto_set_image:
        result += "%s. Image Paint Auto Set Image will be set to True" % queue_number
        result += "\n"
        queue_number += 1

    camera_object = scene.camera
    if (not camera_object) and scene.cpp.has_available_camera_objects:
        camera_object = list(scene.cpp.available_camera_objects)[0]
        result += "%s. Scene camera will be set to %s" % (queue_number, camera_object.name)
        result += "\n"
        queue_number += 1

    if camera_object:
        image = camera_object.data.cpp.image

        if image and image.cpp.valid and (image != image_paint.clone_image):
            result += "%s. Image Paint Clone Image will be set to %s" % (queue_number, image.name)
            result += "\n"
            queue_number += 1

    if not result:
        result = "Context is ready"
    else:
        result += "%s. Lightning method for solid/textured viewport shading will be set to Flat" % queue_number
        result += "\n"
        queue_number += 1

    return result


def operator_execute(self, context):
    """Operator Execution Method"""
    active_object = context.active_object
    scene = context.scene
    image_paint = scene.tool_settings.image_paint

    if active_object.mode != 'TEXTURE_PAINT':
        bpy.ops.object.mode_set(mode='TEXTURE_PAINT')

    tool = context.workspace.tools.from_space_view3d_mode(context.mode, create=False)
    if tool.idname != "builtin_brush.Clone":
        bpy.ops.wm.tool_set_by_id(name="builtin_brush.Clone", cycle=False, space_type='VIEW_3D')

    if image_paint.mode != 'IMAGE':
        image_paint.mode = 'IMAGE'

    if not image_paint.use_clone_layer:
        image_paint.use_clone_layer = True

    if scene.cpp.mapping != 'CAMERA':
        scene.cpp.mapping = 'CAMERA'

    if not scene.cpp.use_auto_set_image:
        scene.cpp.use_auto_set_image = True

    if not scene.camera:
        if scene.cpp.has_available_camera_objects:
            scene.camera = list(scene.cpp.available_camera_objects)[0]

    if scene.camera:
        image = scene.camera.data.cpp.image
        if image:
            if image.cpp.valid:
                image_paint.clone_image = image

    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.light = 'FLAT'

    return {'FINISHED'}


class CPP_OT_enter_context(bpy.types.Operator):
    bl_idname = "cpp.enter_context"
    bl_label = "Setup Context"

    @classmethod
    def poll(cls, context):
        if poll.full_poll(context):
            return False
        active_object = context.active_object
        if not active_object:
            return False
        if active_object.type != 'MESH':
            return False
        scene = context.scene
        if not scene.cpp.has_camera_objects:
            return True
        return True

    @classmethod
    def description(cls, context, properties):
        return operator_description(cls, context, properties)

    execute = operator_execute
