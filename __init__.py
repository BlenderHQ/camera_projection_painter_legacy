# <pep8 compliant>

__all__ = ["bl_info", "register", "unregister"]

bl_info = {
    "name": "Camera Projection Painter",
    "author": "Vlad Kuzmin, Ivan Perevala",
    "version": (0, 1, 2, 6),
    "blender": (2, 80, 0),
    "description": "Expanding capabilities of texture paint Clone Brush",
    "location": "Clone Brush tool settings, Scene tab, Camera tab",
    "wiki_url": "",
    "support": 'COMMUNITY',
    "category": "Paint",
}


if "bpy" in locals():  # In case of module reloading
    import types
    import importlib

    _modules = (
        "handlers",
        "icons",
        "overwrite_ui",
        "shaders",
        "ui",
        "utils",
        "constants",
        "extend_bpy_types",
        "gizmos",
        "keymap",
        "operators",
        "preferences",
    )

    dict_locals = locals().copy()

    func_name = "unregister"
    func = dict_locals.get(func_name)
    assert isinstance(func, types.FunctionType)
    func()

    for item_name, item in dict_locals.items():
        if item_name in _modules and isinstance(item, types.ModuleType):
            importlib.reload(item)

    func_name = "register_at_reload"
    func = dict_locals.get(func_name)
    assert isinstance(func, types.FunctionType)
    func()

    del types
    del importlib
else:
    from . import handlers
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
def load_post_register(dummy = None):
    global _module_registered
    if not _module_registered:
        _module_registered = True
        for module in (
                icons,
                extend_bpy_types,
                keymap,
                overwrite_ui,
                ui,
                operators,
                gizmos):
            reg_func = getattr(module, "register")
            reg_func()

def register_at_reload():
    # Reproduce registration process
    global _module_registered

    _module_registered = False
    register()
    load_post_register()
    handlers.load_post_handler()


def register():
    # Register base loaders at startup
    bpy.utils.register_class(operators.info.CPP_OT_info)
    bpy.utils.register_class(preferences.CppPreferences)

    bpy.app.handlers.load_post.append(load_post_register)
    handlers.register()


def unregister():
    # stop running operators
    global _module_registered

    for op in operators.basis.cpp.modal_ops:
        if hasattr(op, "cancel"):
            op.cancel(bpy.context)

    # call modules unregister
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
