# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(utils)

    del importlib
else:
    from .. import utils

import bpy


class CPP_OT_info(bpy.types.Operator):
    bl_idname = "cpp.info"
    bl_label = "Info"

    text: bpy.props.StringProperty(default = "Info")

    @classmethod
    def description(self, context, properties):
        return properties.text

    def draw(self, context):
        layout = self.layout
        layout.emboss = 'NONE'
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align = True)

        lines = (l for l in str(self.text).splitlines() if l)

        icon_list = ['ERROR', 'INFO']

        for line in lines:
            if line.startswith("https://"):
                col.separator()
                col.operator("wm.url_open", text = line, icon = 'URL').url = line
            else:
                splits = line.split('#')
                tag = splits[0]
                if tag in icon_list:
                    text = "".join(splits[1::])
                    col.label(text = text, icon = splits[0])
                elif tag == "WEB":
                    text = "".join(splits[1::])
                    row = col.row()
                    row.emboss = 'NORMAL'
                    row.operator("wm.url_open", text = text, icon = 'URL').url = text
                else:
                    col.label(text = line)

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self)

    def execute(self, context):
        return {'FINISHED'}
