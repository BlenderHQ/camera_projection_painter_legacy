# <pep8 compliant>

import bpy
from bpy.props import (
    FloatProperty,
    IntProperty,
    EnumProperty,
    FloatVectorProperty
)

import rna_keymap_ui

from . import operators
from .operators import CPP_OT_set_camera_by_view, CPP_OT_image_paint
from .icons import get_icon_id
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
            ('NO_OUTLINE', "No outline", 'Outline not used', "", 0),
            ('FILL', "Fill color", 'Single color outline', get_icon_id("pattern_fill"), 1),
            ('CHECKER', "Checker", 'Checker pattern outline', get_icon_id("pattern_checker"), 2),
            ('LINES', "Lines", 'Lines pattern outline', get_icon_id("pattern_lines"), 3)],
        name = "Type",
        default = 'LINES',
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
        default = [0.784363, 0.735347, 0.787399, 0.792857],
        subtype = "COLOR", size = 4, min = 0.0, max = 1.0,
        description = "Outline color")

    normal_highlight_color: FloatVectorProperty(
        name = "Normal Highlight",
        default = [0.076387, 0.135512, 0.626662, 0.742857],
        subtype = "COLOR", size = 4, min = 0.0, max = 1.0,
        description = "Highlight stretched projection color")

    warning_color: FloatVectorProperty(
        name = "Warning Color",
        default = [1.000000, 0.102228, 0.030697, 1.000000],
        subtype = "COLOR", size = 4, min = 0.0, max = 1.0,
        description = "Highlight brush warning color")

    camera_line_width: FloatProperty(
        name = "Line Width",
        default = 1.0, soft_min = 1.0, soft_max = 5.0,
        subtype = 'PIXEL',
        description = "Width of camera primitive")

    camera_color: FloatVectorProperty(
        name = "Color",
        default = [0.000963, 0.001284, 0.002579, 0.564286],
        subtype = "COLOR", size = 4, min = 0.0, max = 1.0,
        description = "Camera color")

    camera_color_highlight: FloatVectorProperty(
        name = "Color Highlight",
        default = [0.019613, 0.356583, 0.827556, 0.957143],
        subtype = "COLOR", size = 4, min = 0.0, max = 1.0,
        description = "Camera color")

    camera_color_loaded_data: FloatVectorProperty(
        name = "Color Loaded",
        default = [0.062277, 0.092429, 0.246195, 0.714286],
        subtype = "COLOR", size = 4, min = 0.0, max = 1.0,
        description = "Camera image has data loaded into memory")

    # Gizmos
    gizmo_color: FloatVectorProperty(
        name = "Color",
        default = [0.019613, 0.356583, 0.827556, 0.742857],
        subtype = "COLOR", size = 4, min = 0.0, max = 1.0,
        description = "Gizmo color")

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

    def draw(self, context):
        layout = self.layout

        wm = context.window_manager
        if hasattr(wm, "cpp_running"):
            row = layout.row()
            row.prop(self, "tab", expand = True)

            if self.tab == 'INFO':
                self.draw_info_tab(layout)
            elif self.tab == 'DRAW':
                self.draw_draw_tab(layout)
            elif self.tab == 'KEYMAP':
                self.draw_keymap_tab(layout)
        else:
            col = layout.column()
            col.label(text = "Please, reload Blender or current file to begin.")

    def draw_info_tab(self, layout):
        col = layout.column(align = True)
        for name, url in WEB_LINKS:
            col.operator("wm.url_open", text = name, icon = 'URL').url = url

    def draw_draw_tab(self, layout):
        col = layout.column(align = True)

        col.use_property_split = True
        col.use_property_decorate = False

        col.label(text = "Outline:")
        row = col.row()
        # row.use_property_split = False
        row.prop(self, "outline_type", expand = True, emboss = True)
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
        col.separator()
        col.prop(self, "camera_line_width")
        col.prop(self, "camera_color")
        col.prop(self, "camera_color_highlight")
        col.prop(self, "camera_color_loaded_data")

        col.label(text = "Camera Gizmo:")
        col.label(text = "(Updated after refreshing gizmo)")
        col.prop(self, "gizmo_radius")
        col.prop(self, "gizmo_color")

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
