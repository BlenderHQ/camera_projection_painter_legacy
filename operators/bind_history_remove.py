import bpy


class CPP_OT_bind_history_remove(bpy.types.Operator):
    bl_idname = "cpp.bind_history_remove"
    bl_label = "Remove"
    bl_description = "Remove item from image palette list"
    bl_options = {'INTERNAL'}

    index: bpy.props.IntProperty(default=0)

    def execute(self, context):
        if context.mode == 'PAINT_TEXTURE':
            camera_object = context.scene.camera
        elif context.mode == 'OBJECT':
            camera_object = context.active_object
            if camera_object and camera_object.type != 'CAMERA':
                camera_object = None

        if camera_object:
            camera = camera_object.data
            camera.cpp_bind_history.remove(self.index)
            if len(camera.cpp_bind_history):
                camera.cpp.active_bind_index = min(max(self.index - 1, 0), len(camera.cpp_bind_history) - 1)
            return {'FINISHED'}
        else:
            return {'CANCELLED'}
