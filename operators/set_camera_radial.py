# <pep8 compliant>

import importlib
import math

import bpy
from mathutils import Vector

from .. import poll


if "_rc" in locals():
    importlib.reload(poll)

_rc = None


def operator_execute(self, context):
    """Operator Execution Method"""
    scene = context.scene

    initial_camera = scene.camera
    camera_angles = {}

    for camera_object in scene.cpp.available_camera_objects:
        if camera_object.cpp.initial_hide_viewport:
            continue
        mat = camera_object.matrix_world
        x, y, z = -Vector((mat[0][2], mat[1][2], 0.0)).normalized()
        angle = math.atan2(x, y)
        camera_angles[camera_object] = angle

    camera_angles = sorted(camera_angles.items(), key=lambda item: item[1], reverse=True)
    cameras_count = len(camera_angles) - 1

    prev_camera = None
    next_camera = None
    for i, item in enumerate(camera_angles):
        camera_object, angle = item

        if scene.camera == camera_object:
            if i == 0:
                prev_camera = camera_angles[-1][0]
                next_camera = camera_angles[1][0]
            elif i == cameras_count:
                prev_camera = camera_angles[i - 1][0]
                next_camera = camera_angles[0][0]
            else:
                prev_camera = camera_angles[i - 1][0]
                next_camera = camera_angles[i + 1][0]

    if self.order == 'PREV':
        new_camera_object = prev_camera
    elif self.order == 'NEXT':
        new_camera_object = next_camera

    if new_camera_object:
        scene.camera = new_camera_object
        if new_camera_object != initial_camera:
            self.report(type={'INFO'}, message="Set camera %s active" % new_camera_object.name)

    return {'FINISHED'}


class CPP_OT_set_camera_radial(bpy.types.Operator):
    bl_idname = "cpp.set_camera_radial"
    bl_label = "Radial Ordered Cameras Selection"
    bl_options = {'UNDO', 'INTERNAL'}
    bl_description = "Selecting the next camera according to its orientation"

    order: bpy.props.EnumProperty(
        items=[
            ('PREV', "PREV", ""),
            ('NEXT', "NEXT", "")
        ],
        name="mode",
        default='NEXT'
    )

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if not scene.camera:
            return False
        if len(list(scene.cpp.available_camera_objects)) < 2:
            return False
        return poll.tool_setup_poll(context)

    execute = operator_execute
