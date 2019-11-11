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

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, EnumProperty, FloatVectorProperty

from .utils.utils_state import state
from .operators import CPP_OT_set_camera_by_view

WEB_LINKS = [
    ("Help", "https://github.com/ivan-perevala/"),
    ("Youtube tutorial", "https://youtu.be/6ffpaG8KPJk")
]


def get_hotkey_entry_item(km, kmi_name):
    for i, km_item in enumerate(km.keymap_items):
        if km.keymap_items.keys()[i] == kmi_name:
            return km_item


def draw_kmi(kmi, layout):
    row = layout.row()
    row.prop(kmi, "active", text = "", emboss = False)

    row = row.row()
    row.enabled = kmi.active
    row.label(text = kmi.name)
    row.prop(kmi, "type", text = "", full_event = True)
    row.prop(kmi, "value", text = "")


class CppPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    tab: EnumProperty(
        items = [
            ('DRAW', "Draw", 'Viewport draw preferences', 'VIEW3D', 0),
            ('KEYMAP', "Keymap", 'Operators key bindings', 'KEYINGSET', 1),
            ('HELP', "Help", 'Links to documentation and tutorials', 'QUESTION', 2)],
        name = "Tab", default = "HELP")

    # Preview draw
    outline_type: EnumProperty(
        items = [
            ('NO_OUTLINE', "No outline", 'Outline not used', '', 0),
            ('FILL', "Fill color", 'Single color outline', '', 1),
            ('CHECKER', "Checker", 'Checker Pattern outline', '', 2)],
        name = "Type",
        default = 'CHECKER',
        description = "Outline to be drawn outside camera rectangle for preview")

    outline_width: FloatProperty(
        name = "Width",
        default = 0.25,
        soft_min = 0.0,
        soft_max = 5.0,
        description = "Outline width")

    outline_scale: FloatProperty(
        name = "Scale",
        default = 50.0, soft_min = 1.0, soft_max = 100.0,
        description = "Outline scale")

    outline_color: FloatVectorProperty(
        name = "Color",
        default = (0.343402, 0.449120, 0.999984, 0.500000),
        subtype = "COLOR", size = 4, min = 0.0, max = 1.0,
        description = "Outline color")

    normal_highlight_color: FloatVectorProperty(
        name = "Normal Highlight Color",
        default = (0.281741, 0.533584, 1.000000, 0.609286),
        subtype = "COLOR", size = 4, min = 0.0, max = 1.0,
        description = "Highlight stretched projection color")

    warning_color: FloatVectorProperty(
        name = "Warning Color",
        default = (0.223, 0.223, 0.223, 0.95),
        subtype = "COLOR", size = 4, min = 0.0, max = 1.0,
        description = "Highlight brush warning color")

    # Gizmos
    gizmo_color: FloatVectorProperty(
        name = "Color",
        default = (0.281741, 0.533584, 1.000000),
        subtype = "COLOR", size = 3, min = 0.0, max = 1.0,
        description = "Gizmo color")

    gizmo_highlight_color: FloatVectorProperty(
        name = "Highlight Color",
        default = (0.95, 0.95, 0.95),
        subtype = "COLOR", size = 3, min = 0.0, max = 1.0,
        description = "Gizmo highlight color")

    gizmo_passive_color: FloatVectorProperty(
        name = "Passive Color",
        default = (0.5, 0.5, 0.5),
        subtype = "COLOR", size = 3, min = 0.0, max = 1.0,
        description = "Gizmo passive color")

    gizmo_alpha: FloatProperty(
        name = "Alpha",
        default = 1.0, soft_min = 0.1, soft_max = 1.0,
        description = "Gizmo alpha")

    border_empty_space: IntProperty(
        name = "Border Empty Space",
        default = 25, soft_min = 5, soft_max = 100,
        description = "Border Empty Space")

    def draw(self, context):
        layout = self.layout

        if not state.operator:
            layout.label(text = "To finish addon installation please reload current file", icon = 'INFO')
            col = layout.column(align = True)
            col.use_property_split = True
            col.use_property_decorate = False
            self._draw_help(col)
        else:
            row = layout.row()
            row.prop(self, "tab", expand = True)

            col = layout.column(align = True)
            col.use_property_split = True
            col.use_property_decorate = False

            if self.tab == 'HELP':
                self._draw_help(col)
            elif self.tab == 'DRAW':
                self._draw_draw(col)
            elif self.tab == 'KEYMAP':
                self._draw_keymap(col)

    def _draw_help(self, layout):
        for name, url in WEB_LINKS:
            layout.operator("wm.url_open", text = name, icon = 'URL').url = url

    def _draw_draw(self, layout):
        # Outline
        layout.label(text = "Outline:")
        layout.prop(self, "outline_type")
        scol = layout.column(align = True)
        if self.outline_type == 'NO_OUTLINE':
            scol.enabled = False
        scol.prop(self, "outline_width")
        scol.prop(self, "outline_scale")
        scol.prop(self, "outline_color")

        # Outline text
        layout.label(text = "Inspection:")
        layout.prop(self, "normal_highlight_color")
        layout.prop(self, "warning_color")

        layout.separator()
        # Gizmos
        layout.label(text = "Gizmo:")
        scol = layout.column(align = True)
        scol.prop(self, "gizmo_color")
        scol.prop(self, "gizmo_highlight_color")
        scol.prop(self, "gizmo_alpha")

        layout.label(text = "Current Image Preview:")
        scol = layout.column(align = True)
        scol.prop(self, "border_empty_space")

    def _draw_keymap(self, layout):
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.addon
        km = kc.keymaps["3D View"]

        layout.context_pointer_set("keymap", km)

        col = layout.column()
        col.use_property_split = False
        col.use_property_decorate = True

        kmi = get_hotkey_entry_item(km, CPP_OT_set_camera_by_view.bl_idname)
        draw_kmi(kmi, col)

        kmi = get_hotkey_entry_item(km, "view3d.view_center_pick")
        draw_kmi(kmi, col)


def register():
    bpy.utils.register_class(CppPreferences)


def unregister():
    bpy.utils.unregister_class(CppPreferences)
