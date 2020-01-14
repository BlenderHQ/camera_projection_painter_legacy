# <pep8 compliant>

import bpy

def operator_execute(self, context):
    """Operator Execution Method"""
    scene = context.scene
    wm = context.window_manager
    camera_object = wm.cpp_current_selected_camera_ob

    state = not camera_object.cpp.initial_hide_viewport

    camera_object.cpp.initial_hide_viewport = state

    return {'FINISHED'}


class CPP_OT_toggle_camera_usage(bpy.types.Operator):
    bl_idname = "cpp.toggle_camera_usage"
    bl_label = "Toogle Usage"
    bl_options = {'INTERNAL'}

    execute = operator_execute
