# <pep8 compliant>

# The module contains the main addon framework.
# The CPP_OT_listener operator monitors the context of the main operator - CPP_OT_camera_projection_painter
# and starts it when all conditions are met. The main operator starts the tracking operator if the context
# conditions do not match the necessary

if "bpy" in locals():  # In case of module reloading
    import importlib

    importlib.reload(op_methods)

    del importlib
else:
    from . import op_methods

import bpy


class CPP_OT_listener(bpy.types.Operator):
    bl_idname = "cpp.listener"
    bl_label = "Listener"
    bl_options = {'INTERNAL'}

    invoke = op_methods.listener_invoke

    cancel = op_methods.listener_cancel

    modal = op_methods.listener_modal


class CPP_OT_camera_projection_painter(bpy.types.Operator):
    bl_idname = "cpp.camera_projection_painter"
    bl_label = "Camera Projection Painter"
    bl_options = {'INTERNAL'}

    invoke = op_methods.operator_invoke

    cancel = op_methods.operator_cancel

    modal = op_methods.operator_modal
