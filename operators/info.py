# <pep8 compliant>

import bpy


class CPP_OT_info(bpy.types.Operator):
    bl_idname = "cpp.info"
    bl_label = "Info"
    bl_options = {'INTERNAL'}

    text: bpy.props.StringProperty(default = "Info")

    @classmethod
    def description(self, context, properties):
        return properties.text

    def execute(self, context):
        """Operator Execution Method"""
        print(self.text)
        return {'FINISHED'}
