import bpy
import io_scene_fbx


class CPP_PT_fbx_import_include(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        operator = context.space_data.active_operator
        return operator.bl_idname == "CPP_OT_io_fbx"

    draw = io_scene_fbx.FBX_PT_import_include.draw


class CPP_PT_fbx_import_transform(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Transform"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        operator = context.space_data.active_operator
        return operator.bl_idname == "CPP_OT_io_fbx"

    draw = io_scene_fbx.FBX_PT_import_transform.draw


class CPP_PT_fbx_import_transform_manual_orientation(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Manual Orientation"
    bl_parent_id = "FBX_PT_import_transform"

    @classmethod
    def poll(cls, context):
        operator = context.space_data.active_operator
        return operator.bl_idname == "CPP_OT_io_fbx"

    draw_header = io_scene_fbx.FBX_PT_import_transform_manual_orientation.draw_header
    draw = io_scene_fbx.FBX_PT_import_transform_manual_orientation.draw


class CPP_PT_fbx_import_animation(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Animation"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        operator = context.space_data.active_operator
        return operator.bl_idname == "CPP_OT_io_fbx"

    draw_header = io_scene_fbx.FBX_PT_import_animation.draw_header
    draw = io_scene_fbx.FBX_PT_import_animation.draw


class CPP_PT_fbx_import_armature(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Armature"
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        operator = context.space_data.active_operator
        return operator.bl_idname == "CPP_OT_io_fbx"

    draw = io_scene_fbx.FBX_PT_import_armature.draw
