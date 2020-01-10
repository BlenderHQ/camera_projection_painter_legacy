# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(utils)

    del importlib
else:
    from .. import utils

import bpy


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
        return utils.poll.full_poll(context)

    def execute(self, context):
        scene = context.scene
        wm = context.window_manager

        mpos = wm.cpp_mouse_pos
        warning_status = utils.common.get_warning_status(context, mpos)
        if warning_status:
            self.report(type = {'WARNING'}, message = "Danger zone!")
            if scene.cpp.use_warning_action_popup:
                wm.popup_menu(utils.common.danger_zone_popup_menu, title = "Danger zone", icon = 'INFO')
            if scene.cpp.use_warning_action_lock:
                return {'FINISHED'}
        bpy.ops.paint.image_paint('INVOKE_DEFAULT')
        return {'FINISHED'}
