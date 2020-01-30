# <pep8 compliant>

import importlib

import bpy

from .. import poll

if "_rc" in locals():
    importlib.reload(poll)

_rc = None


def operator_execute(self, context):
    """Operator Execution Method"""
    scene = context.scene
    cameras = scene.cpp.available_camera_objects

    for camera_object in cameras:
        camera = camera_object.data

        image = camera.cpp.image
        if not image:
            continue

        width, height = image.cpp.static_size

        if width > height:
            camera.sensor_fit = 'VERTICAL'
        else:
            camera.sensor_fit = 'HORIZONTAL'
        

    return {'FINISHED'}


class CPP_OT_set_all_cameras_sensor(bpy.types.Operator):
    bl_idname = "cpp.set_all_cameras_sensor"
    bl_label = "Sensors To Longest Side"
    bl_options = {'INTERNAL'}
    bl_description = "Sets the type of sensor for all cameras relative to the long side of the binded image"

    @classmethod
    def poll(cls, context):
        return poll.tool_setup_poll(context)

    execute = operator_execute
