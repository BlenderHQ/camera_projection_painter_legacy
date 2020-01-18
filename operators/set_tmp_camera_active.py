# <pep8 compliant>

if "bpy" in locals():  # In case of module reloading
    import importlib

    importlib.reload(utils)

    del importlib
else:
    from . import utils

import bpy


def operator_execute(self, context):
    """Operator Execution Method"""
    scene = context.scene
    wm = context.window_manager

    if scene.cpp.use_auto_set_camera:
        scene.cpp.use_auto_set_camera = False

    scene.camera = wm.cpp_current_selected_camera_ob
    scene.camera.cpp.initial_hide_viewport = False
    for camera_object in scene.cpp.camera_objects:
        if camera_object == scene.camera:
            continue
    if scene.cpp.use_auto_set_image:
        utils.cameras.set_clone_image_from_camera_data(context)

    self.report(type = {'INFO'}, message = "%s is set as active for the scene" % scene.camera.name)

    return {'FINISHED'}

class CPP_OT_set_tmp_camera_active(bpy.types.Operator):
    bl_idname = "cpp.set_tmp_camera_active"
    bl_label = "Set Active"
    bl_description = "Set the camera as active for the scene"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        wm = context.window_manager

        return scene.camera != wm.cpp_current_selected_camera_ob

    execute = operator_execute
