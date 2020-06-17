from . import operators

if "bpy" in locals():
    import importlib
    importlib.reload(operators)

import bpy
import rna_keymap_ui
from bpy.props import (
    BoolProperty,
    FloatProperty,
    IntProperty,
    EnumProperty,
    FloatVectorProperty,
    IntVectorProperty
)

import sys

SUPPORTED_PLATFORMS = ("win32",)
SUPPORTED_BLENDER_VERSION = (2, 83)


readable_platforms = {
    'aix': "AIX",
    'linux': "Linux",
    'win32': "Windows",
    'cygwin': "Windows/Cygwin",
    'darwin': "macOS"
}


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

    # Preview draw
    outline_type: EnumProperty(items=[
        ('NO_OUTLINE', "No outline", "Outline not used" '', 0),
        ('FILL', "Fill color", "Single color outline", '', 1),
        ('CHECKER', "Checker", "Checker pattern outline", '', 2),
        ('LINES', "Lines", "Lines pattern outline", '', 3)
    ],
        name="Type",
        default='LINES',
        description="Outline to be drawn outside camera rectangle for preview")

    outline_width: FloatProperty(
        name="Width",
        default=0.25,
        soft_min=0.0,
        soft_max=5.0,
        subtype='FACTOR',
        description="Outline width")

    outline_scale: FloatProperty(
        name="Scale",
        default=50.0,
        soft_min=1.0,
        soft_max=100.0,
        subtype='FACTOR',
        description="Outline scale")

    outline_color: FloatVectorProperty(
        name="Color",
        default=[0.784363, 0.735347, 0.787399, 0.792857],
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        description="Outline color")

    image_space_color: FloatVectorProperty(
        name="Image Space Color",
        default=[0.013411, 0.013411, 0.013411, 0.950000],
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        description="Color of empty space arround undistorted image")

    normal_highlight_color: FloatVectorProperty(
        name="Normal Highlight",
        default=[0.088655, 0.208637, 0.527115, 0.770000],
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        description="Highlight stretched projection color")

    warning_color: FloatVectorProperty(
        name="Warning Color",
        default=[1.000000, 0.102228, 0.030697, 1.000000],
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        description="Highlight brush warning color")

    camera_line_width: FloatProperty(
        name="Line Width",
        default=0.5,
        soft_min=0.5,
        soft_max=5.0,
        subtype='PIXEL',
        description="Width of camera primitive wireframe")

    active_camera_line_width: FloatProperty(
        name="Active Line Width",
        default=1.5,
        soft_min=0.5,
        soft_max=5.0,
        subtype='PIXEL',
        description="Width of active camera primitive wireframe")

    camera_color: FloatVectorProperty(
        name="Color",
        default=[0.000963, 0.001284, 0.002579, 0.564286],
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        description="Camera color")

    camera_color_highlight: FloatVectorProperty(
        name="Color Highlight",
        default=[0.019613, 0.356583, 0.827556, 0.957143],
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        description="Camera color")

    camera_color_loaded_data: FloatVectorProperty(
        name="Color Loaded",
        default=[0.062277, 0.092429, 0.246195, 0.714286],
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        description="Camera image has data loaded into memory")

    # Gizmos
    gizmo_color: FloatVectorProperty(
        name="Color",
        default=[0.199764, 0.650005, 0.363861, 0.770000],
        subtype="COLOR",
        size=4,
        min=0.0,
        max=1.0,
        description="Gizmo color")

    gizmo_radius: FloatProperty(
        name="Radius",
        default=0.1,
        soft_min=0.1,
        soft_max=1.0,
        subtype='DISTANCE',
        description="Gizmo radius")

    border_empty_space: IntProperty(
        name="Border Empty Space",
        default=25,
        soft_min=5,
        soft_max=100,
        subtype='PIXEL',
        description="Border Empty Space")

    # Defaults
    new_texture_size: IntVectorProperty(
        name="New Texture Size",
        size=2,
        default=(2048, 2048),
        min=512, soft_max=16384,
        description="Width and height for automatically generated textures"
    )

    debug_info: BoolProperty(
        name="Print debug info",
        default=True,
        description="Print information about execution time into console"
    )

    def draw(self, context):
        layout = self.layout
        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user

        is_valid_env = True
        bver = bpy.app.version
        sbver = SUPPORTED_BLENDER_VERSION
        if not (bver[0] == sbver[0] and bver[1] == sbver[1]):
            is_valid_env = False
            layout.label(text=f"""Required Blender version min: "{sbver[0]}.{sbver[1]}" """, icon='FILE_BLEND')
        if sys.platform not in SUPPORTED_PLATFORMS:
            is_valid_env = False
            env_platform = readable_platforms[sys.platform]
            layout.label(text=f"OS {env_platform} currently is unsupported", icon="ERROR")

            str_supported_os = ""
            for i in SUPPORTED_PLATFORMS:
                str_supported_os += readable_platforms[i]
            layout.label(text=f"Supported operating system is {str_supported_os}", icon='INFO')

        if not is_valid_env:
            return

        if not hasattr(wm, "cpp"):
            col = layout.column()
            col.label(text="Please, reload Blender or open any file to begin")
            return

        col_flow = layout.column_flow(columns=2, align=False)
        # Outline
        col = col_flow.column(align=True)
        col.label(text="Outline", icon='SHADING_TEXTURE')
        row = col.row()
        row.prop(self, "outline_type", expand=True, emboss=True)
        scol = col.column(align=True)
        if self.outline_type == 'NO_OUTLINE':
            scol.enabled = False
        scol.prop(self, "outline_width", expand=True)
        scol.prop(self, "outline_scale")
        scol.use_property_split = True
        scol.prop(self, "outline_color")
        scol.prop(self, "image_space_color")
        col.separator()

        # Viewport
        col = col_flow.column(align=True)
        col.label(text="Viewport Inspection", icon='SHADING_RENDERED')
        col.use_property_split = True
        col.prop(self, "normal_highlight_color")
        col.prop(self, "warning_color")
        col.separator()

        # Camera Gizmo
        col = col_flow.column(align=True)
        col.label(text="Camera Gizmo", icon='OUTLINER_OB_CAMERA')
        col.prop(self, "gizmo_radius")
        col.use_property_split = True
        col.prop(self, "gizmo_color")
        col.separator()

        # Current Texture
        col = col_flow.column(align=True)
        col.label(text="Current Texture Gizmo", icon='IMAGE_PLANE')
        scol = col.column(align=True)
        scol.prop(self, "border_empty_space")
        col.separator()

        # Cameras
        col = col_flow.column(align=True)
        col.label(text="Cameras", icon='CAMERA_DATA')
        col.prop(self, "camera_line_width")
        col.prop(self, "active_camera_line_width")
        col.use_property_split = True
        col.prop(self, "camera_color")
        col.prop(self, "camera_color_highlight")
        col.prop(self, "camera_color_loaded_data")
        col.separator()

        # Defaults
        col.label(text="Defaults", icon='FILE_BLANK')
        col.prop(self, "new_texture_size")
        col.prop(self, "debug_info")

        col.separator()

        # Keymap
        layout.label(text="Keymap", icon='KEYINGSET')

        col = layout.column()

        km = kc.keymaps["Image Paint"]

        kmi = get_hotkey_entry_item(km, operators.CPP_OT_image_paint.bl_idname, None, None)
        if kmi:
            col.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)

        kmi = get_hotkey_entry_item(km, "view3d.view_center_pick", None, None)
        if kmi:
            col.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)

        kmi = get_hotkey_entry_item(km, operators.CPP_OT_enable_all_cameras.bl_idname, None, None)
        if kmi:
            col.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
