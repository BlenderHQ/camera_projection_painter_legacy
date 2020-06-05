import bpy


class CPP_OT_toggle_camera_usage(bpy.types.Operator):
    bl_idname = "cpp.toggle_camera_usage"
    bl_label = "Toogle Usage"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        ob = context.window_manager.cpp.current_selected_camera_ob
        return ob and ob.type == 'CAMERA'

    @classmethod
    def description(cls, context, properties):
        ob = context.window_manager.cpp.current_selected_camera_ob
        if ob and ob.initial_visible:
            return "Disable camera"
        else:
            return "Enable camera"

    def execute(self, context):
        ob = context.window_manager.cpp.current_selected_camera_ob
        ob.initial_visible = not ob.initial_visible
        if (context.scene.camera == ob) and (not ob.initial_visible):
            context.scene.camera = None
            self.report(type={'WARNING'}, message="Active camera hidden!")

        return {'FINISHED'}
