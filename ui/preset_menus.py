# <pep8 compliant>

import importlib

import bpy

from .. import presets

if "_rc" in locals():
    importlib.reload(presets)

_rc = None

class CPP_MT_workflow_presets(bpy.types.Menu):
    bl_label = "Workflow Preset"
    preset_subdir = presets.WORKFLOW_PRESETS_DIR_NAME
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset
