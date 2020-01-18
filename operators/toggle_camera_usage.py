# <pep8 compliant>

import bpy

def operator_execute(self, context):
    """Operator Execution Method"""
    scene = context.scene
    wm = context.window_manager
    camera_object = wm.cpp_current_selected_camera_ob

    state = not camera_object.cpp.initial_hide_viewport

    camera_object.cpp.initial_hide_viewport = state

    if state and (scene.camera == camera_object):
        scene.camera = None
        self.report(type = {'WARNING'}, message = "Active camera hidden!")

    return {'FINISHED'}


class CPP_OT_toggle_camera_usage(bpy.types.Operator):
    bl_idname = "cpp.toggle_camera_usage"
    bl_label = "Toogle Usage"
    bl_options = {'INTERNAL'}

    @classmethod
    def description(cls, context, properties):
        scene = context.scene
        wm = context.window_manager
        camera_object = wm.cpp_current_selected_camera_ob

        if camera_object.cpp.initial_hide_viewport:
            return "Enable camera"
        else:
            return "Disable camera"

    execute = operator_execute
