# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

from ..icons import get_icon_id
from .. import operators
from .. import constants


class VIEW3D_PT_tools_brush_clone:
    def draw_header(self, context):
        settings = self.paint_settings(context)
        layout = self.layout
        row = layout.row(align = True)
        row.prop(settings, "use_clone_layer", text = "")

        row.operator(
            operator = operators.CPP_OT_info.bl_idname,
            text = "",
            icon_value = get_icon_id("overwriten")
        ).text = constants.message_overwrite_ui

    def draw(self, context):
        layout = self.layout
        settings = self.paint_settings(context)
        brush = settings.brush

        layout.active = settings.use_clone_layer

        _brush_texpaint_common_clone(self, context, layout, brush, settings, True)


def _brush_texpaint_common_clone(_panel, context, layout, _brush, settings, projpaint = False):  # ScanPaint
    ob = context.active_object
    col = layout.column()

    if settings.mode == 'MATERIAL':
        if len(ob.material_slots) > 1:
            col.label(text = "Materials")
            col.template_list("MATERIAL_UL_matslots", "",
                              ob, "material_slots",
                              ob, "active_material_index", rows = 2)

        mat = ob.active_material
        if mat:
            col.label(text = "Source Clone Slot")
            col.template_list("TEXTURE_UL_texpaintslots", "",
                              mat, "texture_paint_images",
                              mat, "paint_clone_slot", rows = 2)

    elif settings.mode == 'IMAGE':
        # (Rewrite
        scene = context.scene
        mesh = ob.data

        col = col.column()
        col.use_property_split = False
        col.use_property_decorate = False
        mapping = scene.cpp.mapping

        if mapping == 'UV':
            clone_text = mesh.uv_layer_clone.name if mesh.uv_layer_clone else ""
            col.label(text = "Source Clone Image")

            col.template_ID(settings, "clone_image")

            col.label(text = "Source Mapping")
            col.prop(scene.cpp, "mapping", text = "")

            col.label(text = "Source Clone UV Map")
            col.menu("VIEW3D_MT_tools_projectpaint_clone", text = clone_text, translate = False)

        elif mapping == 'CAMERA':
            col.label(text = "Source Clone Image")

            row = col.row(align = True)
            sub_row = row.row()
            sub_row.enabled = not scene.cpp.use_auto_set_image
            sub_row.template_ID(settings, "clone_image")
            icon = "RESTRICT_INSTANCED_OFF" if scene.cpp.use_auto_set_image else "RESTRICT_INSTANCED_ON"
            # sub_row = row.row()
            row.prop(scene.cpp, "use_auto_set_image", toggle = True, text = "", icon = icon)

            col.label(text = "Source Mapping")
            col.prop(scene.cpp, "mapping", text = "")

            col.label(text = "Source Camera")

            row = col.row(align = True)
            sub_row = row.row()
            sub_row.enabled = not scene.cpp.use_auto_set_camera
            sub_row.prop(scene, "camera", text = "")
            icon = "RESTRICT_INSTANCED_OFF" if scene.cpp.use_auto_set_camera else "RESTRICT_INSTANCED_ON"
            row.prop(scene.cpp, "use_auto_set_camera", toggle = True, text = "", icon = icon)
        # )
