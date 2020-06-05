import bpy

from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    EnumProperty,
    CollectionProperty,
)

from bpy_extras.io_utils import (
    ImportHelper,
    orientation_helper,
)

import io_scene_fbx


@orientation_helper(axis_forward='-Z', axis_up='Y')
class CPP_OT_io_fbx(bpy.types.Operator, ImportHelper):
    bl_idname = "cpp.io_fbx"
    bl_label = "Camera Painter Import Fbx"
    bl_options = {'INTERNAL', 'UNDO', 'PRESET'}

    # Copy-paste from .../scripts/addons/io_scene_fbx/__init__.py
    # TODO: Find a way to copy annotation variables (stored in io_scene_fbx.ImportFBX.__annotations__)
    directory: StringProperty()

    filter_glob: StringProperty(default="*.fbx", options={'HIDDEN'})

    files: CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )

    ui_tab: EnumProperty(
        items=(('MAIN', "Main", "Main basic settings"),
               ('ARMATURE', "Armatures", "Armature-related settings"),
               ),
        name="ui_tab",
        description="Import options categories",
    )

    use_manual_orientation: BoolProperty(
        name="Manual Orientation",
        description="Specify orientation and scale, instead of using embedded data in FBX file",
        default=False,
    )
    global_scale: FloatProperty(
        name="Scale",
        min=0.001, max=1000.0,
        default=1.0,
    )
    bake_space_transform: BoolProperty(
        name="!EXPERIMENTAL! Apply Transform",
        description="Bake space transform into object data, avoids getting unwanted rotations to objects when "
        "target space is not aligned with Blender's space "
        "(WARNING! experimental option, use at own risks, known broken with armatures/animations)",
        default=False,
    )

    use_custom_normals: BoolProperty(
        name="Import Normals",
        description="Import custom normals, if available (otherwise Blender will recompute them)",
        default=True,
    )

    use_image_search: BoolProperty(
        name="Image Search",
        description="Search subdirs for any associated images (WARNING: may be slow)",
        default=True,
    )

    use_alpha_decals: BoolProperty(
        name="Alpha Decals",
        description="Treat materials with alpha as decals (no shadow casting)",
        default=False,
    )
    decal_offset: FloatProperty(
        name="Decal Offset",
        description="Displace geometry of alpha meshes",
        min=0.0, max=1.0,
        default=0.0,
    )

    use_anim: BoolProperty(
        name="Import Animation",
        description="Import FBX animation",
        default=True,
    )
    anim_offset: FloatProperty(
        name="Animation Offset",
        description="Offset to apply to animation during import, in frames",
        default=1.0,
    )

    use_subsurf: BoolProperty(
        name="Import Subdivision Surface",
        description="Import FBX subdivision information as subdivision surface modifiers",
        default=False,
    )

    use_custom_props: BoolProperty(
        name="Import User Properties",
        description="Import user properties as custom properties",
        default=True,
    )
    use_custom_props_enum_as_string: BoolProperty(
        name="Import Enums As Strings",
        description="Store enumeration values as strings",
        default=True,
    )

    ignore_leaf_bones: BoolProperty(
        name="Ignore Leaf Bones",
        description="Ignore the last bone at the end of each chain (used to mark the length of the previous bone)",
        default=False,
    )
    force_connect_children: BoolProperty(
        name="Force Connect Children",
        description="Force connection of children bones to their parent, even if their computed head/tail "
        "positions do not match (can be useful with pure-joints-type armatures)",
        default=False,
    )
    automatic_bone_orientation: BoolProperty(
        name="Automatic Bone Orientation",
        description="Try to align the major bone axis with the bone children",
        default=False,
    )
    primary_bone_axis: EnumProperty(
        name="Primary Bone Axis",
        items=(('X', "X Axis", ""),
               ('Y', "Y Axis", ""),
               ('Z', "Z Axis", ""),
               ('-X', "-X Axis", ""),
               ('-Y', "-Y Axis", ""),
               ('-Z', "-Z Axis", ""),
               ),
        default='Y',
    )
    secondary_bone_axis: EnumProperty(
        name="Secondary Bone Axis",
        items=(('X', "X Axis", ""),
               ('Y', "Y Axis", ""),
               ('Z', "Z Axis", ""),
               ('-X', "-X Axis", ""),
               ('-Y', "-Y Axis", ""),
               ('-Z', "-Z Axis", ""),
               ),
        default='X',
    )

    use_prepost_rot: BoolProperty(
        name="Use Pre/Post Rotation",
        description="Use pre/post rotation from FBX transform (you may have to disable that in some cases)",
        default=True,
    )
    # End

    def draw(self, context):
        layout = self.layout

    def cancel(self, context):
        wm = context.window_manager
        wm.cpp.import_state = 'CANCELLED'
        context.window.cursor_modal_restore()

    def invoke(self, context, event):
        wm = context.window_manager
        wm.cpp.import_state = 'FILESELECT'

        # Call standard invoke method
        return ImportHelper.invoke(self, context, event)

    def execute(self, context):
        # Call standard execute method
        context.window.cursor_modal_set('WAIT')
        ret = io_scene_fbx.ImportFBX.execute(self, context)
        context.window.cursor_modal_restore()
        wm = context.window_manager
        wm.cpp.import_dir = self.filepath
        wm.cpp.import_state = 'FINISHED'
        return ret
