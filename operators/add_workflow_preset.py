# <pep8 compliant>

import importlib

import bpy
from bl_operators.presets import AddPresetBase

from .. import presets

if "_rc" in locals():
    importlib.reload(presets)

_rc = None

class CPP_OT_add_workflow_preset(AddPresetBase, bpy.types.Operator):
    '''Add a Object Display Preset'''
    bl_idname = "cpp.add_workflow_preset"
    bl_label = "Add Workflow Preset"
    preset_menu = "CPP_MT_workflow_presets"

    preset_defines = [
        "scene = bpy.context.scene",
        "cpp = scene.cpp"
    ]

    preset_values = [
        #"cpp.mapping",
        "cpp.use_auto_set_image",
        #"cpp.auto_set_camera_method",
        "cpp.use_projection_preview",
        "cpp.use_projection_outline",
        "cpp.use_normal_highlight",
        "cpp.use_camera_image_previews",
        "cpp.use_camera_axes",
        "cpp.use_current_image_preview",
        "cpp.use_warnings",
        "cpp.use_warning_action_draw",
        "cpp.use_warning_action_popup",
        "cpp.use_warning_action_lock",
        "cpp.use_bind_canvas_diffuse",
    ]

    # where to store the preset
    preset_subdir = presets.WORKFLOW_PRESETS_DIR_NAME
