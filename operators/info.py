# <pep8 compliant>

import bpy


class CPP_OT_info(bpy.types.Operator):
    bl_idname = "cpp.info"
    bl_label = "Info"

    text: bpy.props.StringProperty(default = "Info")

    @classmethod
    def description(self, context, properties):
        return properties.text

    def execute(self, context):
        print(self.text)
        return {'FINISHED'}
