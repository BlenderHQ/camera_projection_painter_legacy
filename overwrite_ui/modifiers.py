from ..icons import get_icon_id
from ..constants import TEMP_DATA_NAME


class DATA_PT_modifiers:
    def draw(self, context):
        layout = self.layout

        ob = context.object

        layout.operator_menu_enum("object.modifier_add", "type")

        for md in ob.modifiers:
            # (Added
            if md.name == TEMP_DATA_NAME:
                box = layout.box()
                box.label(text = "Camera Paint (Updated Dynamically)", icon_value = get_icon_id("overwriten"))
                continue
            # )
            box = layout.template_modifier(md)
            if box:
                # match enum type to our functions, avoids a lookup table.
                getattr(self, md.type)(box, ob, md)
