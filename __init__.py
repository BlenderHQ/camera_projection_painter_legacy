# <pep8 compliant>

bl_info = {
    "name": "Camera Projection Painter",
    "author": "Vlad Kuzmin, Ivan Perevala",
    "version": (0, 1, 2, 2),
    "blender": (2, 80, 0),
    "description": "Expanding capabilities of texture paint Clone Brush",
    "location": "Clone Brush tool settings, Scene tab, Camera tab",
    "wiki_url": "",
    "support": 'COMMUNITY',
    "category": "Paint",
}

# Notes:
#       - The addon supports live reloading of the module using importlib.reload (...).
#   The standard operator bpy.ops.script.reload()
#   is not supported because it is not possible while the modal operators work.
#       - To simplify the re-import of submodules,
#   they do not use "from some_module import name" for other submodules,
#   only full import is used.
#       - Main classes are registered only after bpy.app.handlers.load_post is triggered,
#   since only after it is automatic start possible
#

if "bpy" in locals():
    import importlib
    unregister()

    importlib.reload(icons)
    importlib.reload(overwrite_ui)
    importlib.reload(shaders)
    importlib.reload(ui)
    importlib.reload(utils)
    importlib.reload(constants)
    importlib.reload(extend_bpy_types)
    importlib.reload(gizmos)
    importlib.reload(keymap)
    importlib.reload(operators)
    importlib.reload(preferences)

    _module_registered = False
    register()
    _load_post_register(None)
    _load_post_handler(None)

    del importlib

else:
    from . import icons
    from . import overwrite_ui
    from . import shaders
    from . import ui
    from . import utils
    from . import constants
    from . import extend_bpy_types
    from . import gizmos
    from . import keymap
    from . import operators
    from . import preferences

    _module_registered = False

import bpy
from bpy.app.handlers import persistent


@persistent
def _load_post_register(dummy):
    global _module_registered
    if not _module_registered:
        _module_registered = True
        for module in (
                extend_bpy_types,
                keymap,
                overwrite_ui,
                ui,
                operators,
                gizmos):
            reg_func = getattr(module, "register")
            reg_func()


@persistent
def _load_post_handler(dummy):
    # start listener
    wm = bpy.context.window_manager
    wm.cpp_running = False
    wm.cpp_suspended = False
    bpy.ops.cpp.listener('INVOKE_DEFAULT')


@persistent
def _save_pre_handler(dummy):
    wm = bpy.context.window_manager
    if wm.cpp_running:
        bpy.context.scene.cpp.cameras_hide_set(state = False)


@persistent
def _save_post_handler(dummy):
    from .utils import poll
    if poll.full_poll(bpy.context):
        bpy.context.scene.cpp.cameras_hide_set(state = True)


_handlers = [
    (bpy.app.handlers.load_post, _load_post_register),
    (bpy.app.handlers.load_post, _load_post_handler),
    (bpy.app.handlers.save_pre, _save_pre_handler),
    (bpy.app.handlers.save_post, _save_post_handler)
]


def _register_handlers():
    for handle, func in _handlers:
        handle.append(func)


def _unregister_handlers():
    for handle, func in _handlers:
        if func in handle:
            handle.remove(func)


def register():
    from . import operators
    from . import preferences
    bpy.utils.register_class(operators.CPP_OT_info)
    bpy.utils.register_class(preferences.CppPreferences)

    _register_handlers()


def unregister():
    # stop running operators
    global _module_registered
    # call modules unregister
    from . import operators

    for op in operators.modal_ops:
        if hasattr(op, "cancel"):
            try:
                op.cancel(bpy.context)
            except:
                import traceback
                print(traceback.format_exc())
    for module in (icons, overwrite_ui, keymap, extend_bpy_types, ui,
                   operators,
                   gizmos):
        unreg_func = getattr(module, "unregister")
        unreg_func()
    # classes factory
    bpy.utils.unregister_class(operators.CPP_OT_info)
    bpy.utils.unregister_class(preferences.CppPreferences)
    # handlers
    _unregister_handlers()

    _module_registered = False
