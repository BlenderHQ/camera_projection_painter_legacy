# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(utils)

    del importlib
else:
    from .. import utils

import bpy


class CPP_OT_free_memory(bpy.types.Operator):
    bl_idname = "cpp.free_memory"
    bl_label = "Free Memory"
    bl_description = "Free unused images from memory"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        if utils.draw.get_loaded_images_count() > 2:
            return True
        return False

    def execute(self, context):
        scene = context.scene
        image_paint = scene.tool_settings.image_paint

        count = 0
        for image in bpy.data.images:
            if image not in (image_paint.canvas, image_paint.clone_image):
                if image.has_data:
                    image.buffers_free()
                    count += 1

        self.report(type = {'INFO'}, message = "Freed %d images" % count)

        return {'FINISHED'}
