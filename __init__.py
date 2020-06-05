import sys

SUPPORTED_BVER = (2, 83)

if not sys.platform.startswith("win32"):
    raise ImportError("Camera Projection Painter currently available only on Windows")

__all__ = ["bl_info", "register", "unregister"]

bl_info = {
    "name": "Camera Projection Painter",
    "author": "Vlad Kuzmin, Ivan Perevala",
    "version": (0, 1, 3, 2),
    "blender": (2, 80, 0),
    "description": "Expanding the capabilities of clone brush for working with photo scans (alpha)",
    "location": "Tool settings > Camera Painter",
    "support": 'COMMUNITY',
    "category": "Paint",
}

from . import preferences
from . import operators
from . import keymap
from . import gizmos
from . import extend_bpy_types
from . import ui
from . import shaders
from . import handlers
from . import engine


if "bpy" in locals():  # In case of module reloading
    unregister()

    import importlib
    importlib.reload(preferences)
    importlib.reload(operators)
    importlib.reload(keymap)
    importlib.reload(gizmos)
    importlib.reload(extend_bpy_types)
    importlib.reload(ui)
    importlib.reload(handlers)
    importlib.reload(shaders)

    register_at_reload()
else:
    _module_registered = False

import bpy
from bpy.app.handlers import persistent

bver = bpy.app.version
if (bver[0] != SUPPORTED_BVER[0]) or (bver[1] < SUPPORTED_BVER[1]):
    raise ImportError(f"Unsupported Blender version: {bpy.app.version_string}")


def register_at_reload():
    global _module_registered
    _module_registered = False
    register()
    load_post_register()
    handlers.load_post_handler()


_reg_modules = [
    extend_bpy_types,
    ui,
    operators,
    keymap,
    gizmos,
    handlers
]


@persistent
def load_post_register(dummy=None):
    global _module_registered
    if not _module_registered:
        _module_registered = True
        for module in _reg_modules:
            reg_func = getattr(module, "register")
            reg_func()


def register():
    bpy.utils.register_class(preferences.CppPreferences)
    bpy.app.handlers.load_post.append(load_post_register)


def unregister():
    global _module_registered

    for op in operators.basis.modal_ops:
        if hasattr(op, "cancel"):
            op.cancel(bpy.context)

    for module in reversed(_reg_modules):
        unreg_func = getattr(module, "unregister")
        unreg_func()

    bpy.utils.unregister_class(preferences.CppPreferences)

    # handlers
    if load_post_register in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post_register)
    handlers.unregister()

    _module_registered = False
