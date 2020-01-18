# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(poll)

    del importlib
else:
    from .. import poll

import bpy


def operator_execute(self, context):
    """Operator Execution Method"""
    scene = context.scene
    enabled_count = 0
    for camera_object in scene.cpp.camera_objects:
        camera_object.cpp.initial_hide_viewport = False
        enabled_count += 1

    if enabled_count:
        self.report(type = {'INFO'}, message = "Enabled %d cameras" % enabled_count)
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

    return {'FINISHED'}

class CPP_OT_enable_all_cameras(bpy.types.Operator):
    bl_idname = "cpp.enable_all_cameras"
    bl_label = "Enable All Cameras"
    bl_options = {'INTERNAL'}
    bl_description = "Sets all cameras in the scene as used for automation"

    @classmethod
    def poll(cls, context):
        return poll.tool_setup_poll(context)

    execute = operator_execute
