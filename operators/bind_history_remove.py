# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(utils)

    del importlib
else:
    from .. import utils

import bpy


class CPP_OT_bind_history_remove(bpy.types.Operator):
    bl_idname = "cpp.bind_history_remove"
    bl_label = "Remove Image From List"
    bl_options = {'INTERNAL'}

    mode: bpy.props.EnumProperty(
        items = [('CONTEXT', "Context", ""),
                 ('TMP', "Tmp", "")],
        name = "Mode",
        default = 'CONTEXT')

    def execute(self, context):
        scene = context.scene
        if self.mode == 'CONTEXT':
            camera_ob = scene.camera
        else:
            # 'TMP'
            wm = context.window_manager
            camera_ob = wm.cpp_current_selected_camera_ob

        camera = camera_ob.data
        bind_history = camera.cpp_bind_history
        active_bind_index = camera.cpp.active_bind_index
        bind_history.remove(active_bind_index)
        if len(camera.cpp_bind_history):
            camera.cpp.active_bind_index = len(camera.cpp_bind_history) - 1
        return {'FINISHED'}
