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
from bpy.props import (
    BoolProperty,
    FloatProperty,
    IntProperty,
    EnumProperty,
    FloatVectorProperty
)

import rna_keymap_ui

from .utils.utils_state import state
from .operators import CPP_OT_set_camera_by_view, CPP_OT_image_paint
from .constants import WEB_LINKS


def get_hotkey_entry_item(km, kmi_name, kmi_value, properties):
    for i, km_item in enumerate(km.keymap_items):
        if km.keymap_items.keys()[i] == kmi_name:
            if properties:
                value = getattr(km.keymap_items[i].properties, properties, None)
                if value == kmi_value:
                    return km_item
            else:
                return km_item


class CppPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    tab: EnumProperty(
        items = [
            ('DRAW', "Draw", 'Viewport draw preferences'),
            ('KEYMAP', "Keymap", 'Operators key bindings'),
            ('INFO', "Info", 'Links to documentation and tutorials')],
        name = "Tab", default = "DRAW")

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
        default = 0.25, soft_min = 0.0, soft_max = 5.0,
        subtype = 'FACTOR',
        description = "Outline width")

    outline_scale: FloatProperty(
        name = "Scale",
        default = 50.0, soft_min = 1.0, soft_max = 100.0,
        subtype = 'FACTOR',
        description = "Outline scale")

    outline_color: FloatVectorProperty(
        name = "Color",
        default = (0.343402, 0.449120, 0.999984, 0.500000),
        subtype = "COLOR", size = 4, min = 0.0, max = 1.0,
        description = "Outline color")

    normal_highlight_color: FloatVectorProperty(
        name = "Normal Highlight",
        default = (0.281741, 0.533584, 1.000000, 0.609286),
        subtype = "COLOR", size = 4, min = 0.0, max = 1.0,
        description = "Highlight stretched projection color")

    warning_color: FloatVectorProperty(
        name = "Warning Color",
        default = (0.223, 0.223, 0.223, 0.95),
        subtype = "COLOR", size = 4, min = 0.0, max = 1.0,
        description = "Highlight brush warning color")

    camera_line_width: FloatProperty(
        name = "Line Width",
        default = 1.0, soft_min = 1.0, soft_max = 5.0,
        subtype = 'PIXEL',
        description = "Width of camera primitive")

    camera_color: FloatVectorProperty(
        name = "Color",
        default = (0.0, 0.0, 0.0, 0.8),
        subtype = "COLOR", size = 4, min = 0.0, max = 1.0,
        description = "Camera color")

    camera_color_highlight: FloatVectorProperty(
        name = "Color Highlight",
        default = (1.0, 0.5, 0.25, 0.8),
        subtype = "COLOR", size = 4, min = 0.0, max = 1.0,
        description = "Camera color")

    # Gizmos
    gizmo_color: FloatVectorProperty(
        name = "Color",
        default = (0.281741, 0.533584, 1.000000),
        subtype = "COLOR", size = 3, min = 0.0, max = 1.0,
        description = "Gizmo color")

    gizmo_alpha: FloatProperty(
        name = "Alpha",
        default = 1.0, soft_min = 0.1, soft_max = 1.0,
        subtype = 'FACTOR',
        description = "Gizmo alpha")

    gizmo_radius: FloatProperty(
        name = "Circle Radius",
        default = 0.1, soft_min = 0.1, soft_max = 1.0,
        subtype = 'DISTANCE',
        description = "Gizmo radius")

    border_empty_space: IntProperty(
        name = "Border Empty Space",
        default = 25, soft_min = 5, soft_max = 100,
        subtype = 'PIXEL',
        description = "Border Empty Space")

    render_preview_size: IntProperty(
        name = "Image previews size",
        default = 128, min = 128, soft_max = 512,
        subtype = 'PIXEL',
        description = "Image previews size")

    def draw(self, context):
        layout = self.layout

        if not state.operator:
            layout.label(text = "To finish addon installation please reload current file", icon = 'INFO')
            col = layout.column(align = True)
            col.use_property_split = True
            col.use_property_decorate = False
            self.draw_info_tab(col)
        else:
            row = layout.row()
            row.prop(self, "tab", expand = True)

            if self.tab == 'INFO':
                self.draw_info_tab(layout)
            elif self.tab == 'DRAW':
                self.draw_draw_tab(layout)
            elif self.tab == 'KEYMAP':
                self.draw_keymap_tab(layout)

    def draw_info_tab(self, layout):
        col = layout.column(align = True)
        for name, url in WEB_LINKS:
            col.operator("wm.url_open", text = name, icon = 'URL').url = url

    def draw_draw_tab(self, layout):
        col = layout.column(align = True)

        col.use_property_split = True
        col.use_property_decorate = False

        col.label(text = "Viewport Projection Border Outline:")
        col.prop(self, "outline_type")
        scol = col.column(align = True)
        if self.outline_type == 'NO_OUTLINE':
            scol.enabled = False
        scol.prop(self, "outline_width")
        scol.prop(self, "outline_scale")
        scol.prop(self, "outline_color")

        col.label(text = "Viewport Inspection:")
        col.prop(self, "normal_highlight_color")
        col.prop(self, "warning_color")

        col.label(text = "Cameras:")
        col.prop(self, "render_preview_size")
        col.separator()
        col.prop(self, "camera_line_width")
        col.prop(self, "camera_color")
        col.prop(self, "camera_color_highlight")

        col.label(text = "Camera Gizmo:")
        col.label(text = "(Updated after refreshing gizmo)")
        col.prop(self, "gizmo_radius")
        col.prop(self, "gizmo_color")
        col.prop(self, "gizmo_alpha")

        col.label(text = "Current Image Preview Gizmo:")
        scol = col.column(align = True)
        scol.prop(self, "border_empty_space")

    def draw_keymap_tab(self, layout):
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user

        col = layout.column()

        km = kc.keymaps["Image Paint"]

        kmi = get_hotkey_entry_item(km, CPP_OT_image_paint.bl_idname, None, None)
        if kmi:
            col.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)

        kmi = get_hotkey_entry_item(km, CPP_OT_set_camera_by_view.bl_idname, None, None)
        if kmi:
            col.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)

        kmi = get_hotkey_entry_item(km, "view3d.view_center_pick", None, None)
        if kmi:
            col.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)

        col.separator()

        kmi = get_hotkey_entry_item(km, "wm.context_toggle", "scene.cpp.use_camera_image_previews", "data_path")
        if kmi:
            col.context_pointer_set("keymap", km)
            col.label(text = "Camera Image Previews:")
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)

        kmi = get_hotkey_entry_item(km, "wm.context_toggle", "scene.cpp.use_projection_preview", "data_path")
        if kmi:
            col.context_pointer_set("keymap", km)
            col.label(text = "Projection Preview:")
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)

        kmi = get_hotkey_entry_item(km, "wm.context_toggle", "scene.cpp.use_current_image_preview", "data_path")
        if kmi:
            col.context_pointer_set("keymap", km)
            col.label(text = "Current Image Preview:")
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)




# kmi = get_hotkey_entry_item(km, CPP_OT_image_paint.bl_idname)
# draw_kmi(kmi, col)


#
# kmi = get_hotkey_entry_item(km, CPP_OT_set_camera_by_view.bl_idname)
# draw_kmi(kmi, col)
#
# kmi = get_hotkey_entry_item(km, "view3d.view_center_pick")
# draw_kmi(kmi, col)
#
# kmi = get_hotkey_entry_item(
#    km, "wm.context_toggle",
#    properties = {"data_path": "scene.cpp.use_camera_image_previews"})
# draw_kmi(kmi, col, text = "Toggle Camera Image Previews")
#
# kmi = get_hotkey_entry_item(
#    km, "wm.context_toggle",
#    properties = {"data_path": "scene.cpp.use_projection_preview"})
# draw_kmi(kmi, col, text = "Toggle Projection Preview")
#
# kmi = get_hotkey_entry_item(
#    km, "wm.context_toggle",
#    properties = {"data_path": "scene.cpp.use_current_image_preview"})
# draw_kmi(kmi, col, text = "Toggle Current Image Preview")
#

_classes = [
    CppPreferences,
]
register, unregister = bpy.utils.register_classes_factory(_classes)
