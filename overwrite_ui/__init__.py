# <pep8 compliant>

# Some parts of the user interface are overwritten so as not to show the user
# unnecessary information about objects, tools, etc

import importlib
import inspect

import bpy
import bl_ui

from . import constants
from . import mesh_data
from . import tool_brush_clone

if "_rc" in locals():  # In case of module reloading
    importlib.reload(constants)
    importlib.reload(mesh_data)
    importlib.reload(tool_brush_clone)

_rc = None


_classes = [
    mesh_data.DATA_PT_uv_texture,
    mesh_data.MESH_UL_uvmaps,
    tool_brush_clone.VIEW3D_PT_tools_brush_clone
]


def register():
    # Overwriting the corresponding methods of the Panel, UIList, Menu, Header standard subclasses
    _overwrite_types = (
        bpy.types.Panel,
        bpy.types.UIList,
        bpy.types.Menu,
        bpy.types.Header)

    for _ in _overwrite_types:
        for sub_class in _.__subclasses__():
            for overwrite_cls in _classes:
                if sub_class.__name__ == overwrite_cls.__name__:
                    overwriten_functions = inspect.getmembers(sub_class, predicate=inspect.isfunction)
                    for func_name, func in overwriten_functions:
                        if func_name in dir(overwrite_cls):
                            new_func = getattr(overwrite_cls, func_name)
                            setattr(sub_class, func_name, new_func)


def unregister():
    # Rebooting the bl_ui module and re-registering it to restore the standard user interface after
    # unregistering the add-on (and also when rebooting the add-on as a module)
    import importlib
    importlib.reload(bl_ui)

    bl_ui.register()
