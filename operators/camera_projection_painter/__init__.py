# <pep8 compliant>

# The submodule contains the main addon framework.
# The CPP_OT_listener operator monitors the context of the main operator - CPP_OT_camera_projection_painter
# and starts it when all conditions are met. The main operator starts the tracking operator if the context
# conditions do not match the necessary

if "bpy" in locals():  # In case of module reloading
    import importlib

    importlib.reload(cpp)

    del importlib
else:
    from . import cpp

import bpy


class CPP_OT_listener(bpy.types.Operator):
    bl_idname = "cpp.listener"
    bl_label = "Listener"
    bl_options = {'INTERNAL'}

    invoke = cpp.listener_invoke

    cancel = cpp.listener_cancel

    modal = cpp.listener_modal


class CPP_OT_camera_projection_painter(bpy.types.Operator):
    bl_idname = "cpp.camera_projection_painter"
    bl_label = "Camera Projection Painter"
    bl_options = {'INTERNAL'}

    invoke = cpp.invoke

    cancel = cpp.cancel

    modal = cpp.modal
