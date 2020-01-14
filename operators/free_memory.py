# <pep8 compliant>

import bpy


def operator_execute(self, context):
    """Operator Execution Method"""
    scene = context.scene
    image_paint = scene.tool_settings.image_paint

    freed_count = 0
    for image in bpy.data.images:
        if image not in (image_paint.canvas, image_paint.clone_image):
            if image.has_data:
                image.buffers_free()
                freed_count += 1

    self.report(type = {'INFO'}, message = "Freed %d images data from memmory" % freed_count)

    return {'FINISHED'}


class CPP_OT_free_memory(bpy.types.Operator):
    bl_idname = "cpp.free_memory"
    bl_label = "Free Memory"
    bl_description = "Frees extra images from memory"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        loaded_images_count = len([n for n in bpy.data.images if n.has_data])
        return loaded_images_count > 2
    
    execute = operator_execute
