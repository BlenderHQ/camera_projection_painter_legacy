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
        if self.camera_name in context.scene.objects:
            ob = context.scene.objects[self.camera_name]
            wm = context.window_manager
            wm.cpp.current_selected_camera_ob = ob
            bpy.ops.wm.call_menu_pie(name="CPP_MT_camera_pie")
            return {'FINISHED'}
        return {'CANCELLED'}
