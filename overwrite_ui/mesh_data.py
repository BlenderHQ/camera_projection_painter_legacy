from ..icons import get_icon_id
from ..constants import TEMP_DATA_NAME


class MESH_UL_uvmaps:
    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        # assert(isinstance(item, (bpy.types.MeshTexturePolyLayer, bpy.types.MeshLoopColorLayer)))
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # (
            if item.name == TEMP_DATA_NAME:
                layout.label(text = "Camera Paint (Updated Dynamically)", icon_value = get_icon_id("overwriten"))
                return
            # )
            layout.prop(item, "name", text = "", emboss = False, icon = 'GROUP_UVS')
            icon = 'RESTRICT_RENDER_OFF' if item.active_render else 'RESTRICT_RENDER_ON'
            layout.prop(item, "active_render", text = "", icon = icon, emboss = False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text = "", icon_value = icon)
