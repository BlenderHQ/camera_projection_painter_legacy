# <pep8 compliant>

import bpy


class CPP_OT_call_pie(bpy.types.Operator):
    bl_idname = "cpp.call_pie"
    bl_label = "CPP Call Pie"
    bl_options = {'INTERNAL'}

    camera_name: bpy.props.StringProperty()

    @classmethod
    def description(self, context, properties):
        text = "Camera: %s" % properties.camera_name
        return text

    def execute(self, context):
        scene = context.scene

        if self.camera_name in scene.objects:
            ob = scene.objects[self.camera_name]
            if ob.type == 'CAMERA':
                wm = context.window_manager
                wm.cpp_current_selected_camera_ob = ob
                bpy.ops.wm.call_menu_pie(name = "CPP_MT_camera_pie")
        return {'FINISHED'}
