from .. import engine
import bpy


class CPP_OT_refresh_image_preview(bpy.types.Operator):
    bl_idname = "cpp.refresh_image_preview"
    bl_label = "Refresh Previews"
    bl_options = {'INTERNAL'}

    skip_already_set: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        engine.updateImageSeqPreviews(list(bpy.data.images), self.skip_already_set, False)
        return {'FINISHED'}
