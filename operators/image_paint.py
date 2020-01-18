# <pep8 compliant>

if "bpy" in locals():  # In case of module reloading
    import importlib

    importlib.reload(utils)
    importlib.reload(constants)
    importlib.reload(poll)

    del importlib
else:
    from . import utils
    from .. import constants
    from .. import poll

import bpy


def operator_execute(self, context):
    """Operator Execution Method"""
    scene = context.scene
    wm = context.window_manager

    mouse_position = wm.cpp_mouse_pos
    warning_status = utils.warnings.get_warning_status(context, mouse_position)

    if warning_status:
        self.report(type = {'WARNING'}, message = "Danger zone!")
        if scene.cpp.use_warning_action_popup:
            wm.popup_menu(utils.warnings.danger_zone_popup_menu, title = "Danger zone", icon = 'INFO')
        if scene.cpp.use_warning_action_lock:
            return {'FINISHED'}

    bpy.ops.paint.image_paint('INVOKE_DEFAULT')

    return {'FINISHED'}


class CPP_OT_image_paint(bpy.types.Operator):
    bl_idname = "cpp.image_paint"
    bl_label = "Image Paint"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if not scene.cpp.use_warnings:
            return False
        if context.area.type != 'VIEW_3D':
            return False
        return poll.full_poll(context)

    execute = operator_execute
