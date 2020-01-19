# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(utils)

    del importlib
else:
    from . import utils

import bpy

operator_description = """Automatically sets the camera with an active projector 
if its orientation and position is close to the viewer"""

def operator_execute(self, context):
    """Operator Execution Method"""
    wm = context.window_manager
    utils.cameras.set_camera_by_view(context, wm.cpp_mouse_pos)
    return {'FINISHED'}


class CPP_OT_set_camera_by_view(bpy.types.Operator):
    bl_idname = "cpp.set_camera_by_view"
    bl_label = "Set camera by view"
    bl_description = operator_description
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        return scene.cpp.has_available_camera_objects

    execute = operator_execute