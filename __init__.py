# <pep8 compliant>

__all__ = ["bl_info", "register", "unregister"]

bl_info = {
    "name": "Camera Projection Painter",
    "author": "Vlad Kuzmin, Ivan Perevala",
    "version": (0, 1, 3, 1),
    "blender": (2, 80, 0),
    "description": "Expanding the capabilities of clone brush for working with photo scans (alpha)",
    "location": "Tool settings > Camera Painter",
    "wiki_url": "",  # TODO: wiki
    "support": 'COMMUNITY',
    "category": "Paint",
}

import time
import importlib

import bpy
from bpy.app.handlers import persistent

from . import preferences
from . import operators
from . import keymap
from . import gizmos
from . import extend_bpy_types
from . import ui
from . import shaders
from . import overwrite_ui
from . import handlers
from . import icons
from . import presets


if "_rc" in locals():  # In case of module reloading
    unregister()

    importlib.reload(icons)
    importlib.reload(preferences)
    importlib.reload(operators)
    importlib.reload(keymap)
    importlib.reload(gizmos)
    importlib.reload(extend_bpy_types)
    importlib.reload(ui)
    importlib.reload(shaders)
    importlib.reload(overwrite_ui)
    importlib.reload(handlers)
    importlib.reload(presets)

    register_at_reload()
else:
    _module_registered = False

_rc = None


def register_at_reload():
    # Reproduce registration process
    global _module_registered
    _module_registered = False
    register()
    load_post_register()
    handlers.load_post_handler()


@persistent
def load_post_register(dummy=None):
    global _module_registered
    if not _module_registered:
        _module_registered = True
        for module in (
                extend_bpy_types,
                overwrite_ui,
                ui,
                operators,
                keymap,
                gizmos,
                handlers,
                presets):
            reg_func = getattr(module, "register")
            reg_func()


def register():
    # Register base loaders at startup
    bpy.utils.register_class(operators.info.CPP_OT_info)
    bpy.utils.register_class(preferences.CppPreferences)

    bpy.app.handlers.load_post.append(load_post_register)


def unregister():
    global _module_registered

    # Stop running operators
    for op in operators.basis.op_methods.modal_ops:
        if hasattr(op, "cancel"):
            op.cancel(bpy.context)

    # Call modules unregister
    for module in (icons, overwrite_ui, keymap, extend_bpy_types, ui,
                   operators,
                   gizmos):
        unreg_func = getattr(module, "unregister")
        unreg_func()

    # classes factory
    bpy.utils.unregister_class(operators.info.CPP_OT_info)
    bpy.utils.unregister_class(preferences.CppPreferences)

    # handlers
    if load_post_register in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(load_post_register)
    handlers.unregister()

    _module_registered = False
