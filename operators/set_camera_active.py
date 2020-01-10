# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(utils)

    del importlib
else:
    from .. import utils

import bpy


class CPP_OT_set_camera_active(bpy.types.Operator):
    bl_idname = "cpp.set_camera_active"
    bl_label = "Set Active"
    bl_description = "Set camera as active projector"

    @classmethod
    def poll(cls, context):
        scene = context.scene

        wm = context.window_manager

        if scene.camera == wm.cpp_current_selected_camera_ob:
            return False
        return True

    def execute(self, context):
        scene = context.scene
        wm = context.window_manager

        if scene.cpp.use_auto_set_camera:
            scene.cpp.use_auto_set_camera = False
        scene.camera = wm.cpp_current_selected_camera_ob
        for camera in scene.cpp.camera_objects:
            if camera == scene.camera:
                continue
        if scene.cpp.use_auto_set_image:
            utils.common.set_clone_image_from_camera_data(context)
        self.report(type = {'INFO'}, message = "%s set active" % scene.camera.name)
        return {'FINISHED'}
