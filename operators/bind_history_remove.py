# <pep8 compliant>

import bpy


operator_mode = bpy.props.EnumProperty(
    items = [
        ('CONTEXT', "Context", ""),
        ('TMP', "Tmp", ""),
        ('ACTIVE', "Active", "")
    ],
    name = "Mode",
    default = 'CONTEXT'
)

def operator_execute(self, context):
    """Operator Execution Method"""
    scene = context.scene
    if self.mode == 'CONTEXT':
        camera_object = scene.camera
    elif self.mode == 'ACTIVE':
        camera_object = context.active_object
    else:  # 'TMP'
        wm = context.window_manager
        camera_object = wm.cpp_current_selected_camera_ob

    camera = camera_object.data
    camera_bind_history = camera.cpp_bind_history
    camera_active_bind_index = camera.cpp.active_bind_index
    camera_bind_history.remove(camera_active_bind_index)
    if len(camera.cpp_bind_history):
        camera.cpp.active_bind_index = len(camera.cpp_bind_history) - 1
    return {'FINISHED'}


class CPP_OT_bind_history_remove(bpy.types.Operator):
    bl_idname = "cpp.bind_history_remove"
    bl_label = "Remove"
    bl_description = "Remove item from image palette list"
    bl_options = {'INTERNAL'}

    mode: operator_mode

    execute = operator_execute
