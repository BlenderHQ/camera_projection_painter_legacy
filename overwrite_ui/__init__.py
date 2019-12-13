import bpy
import bl_ui

import inspect
import importlib

from .mesh_data import DATA_PT_uv_texture, MESH_UL_uvmaps
from .tool_brush_clone import VIEW3D_PT_tools_brush_clone

_classes = [
    DATA_PT_uv_texture,
    MESH_UL_uvmaps,
    VIEW3D_PT_tools_brush_clone
]


def register():
    _overwrite_types = (
        bpy.types.Panel,
        bpy.types.UIList,
        bpy.types.Menu,
        bpy.types.Header)

    for _ in _overwrite_types:
        for sub_class in _.__subclasses__():
            for overwrite_cls in _classes:
                if sub_class.__name__ == overwrite_cls.__name__:
                    overwriten_functions = inspect.getmembers(sub_class, predicate = inspect.isfunction)
                    for func_name, func in overwriten_functions:
                        if func_name in dir(overwrite_cls):
                            new_func = getattr(overwrite_cls, func_name)
                            setattr(sub_class, func_name, new_func)


def unregister():
    importlib.reload(bl_ui)
    bl_ui.register()
