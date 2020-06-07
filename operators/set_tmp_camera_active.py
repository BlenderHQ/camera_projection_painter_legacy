import bpy


class CPP_OT_set_tmp_camera_active(bpy.types.Operator):
    bl_idname = "cpp.set_tmp_camera_active"
    bl_label = "Set Active"
    bl_description = "Set the camera as active for the scene"
    bl_options = {'INTERNAL'}

    __slots__ = ()

    @classmethod
    def poll(cls, context):
        scene = context.scene
        wm = context.window_manager
        return scene.camera != wm.cpp.current_selected_camera_ob

    def execute(self, context):
        scene = context.scene

        ob = context.window_manager.cpp.current_selected_camera_ob
        if ob and ob.type == 'CAMERA':
            scene.camera = ob
            scene.camera.initial_visible = True

            image = ob.data.cpp.image
            if image and image.cpp.valid:
                image_paint = scene.tool_settings.image_paint
                if image_paint.clone_image != image:
                    image_paint.clone_image = image

        return {'FINISHED'}
