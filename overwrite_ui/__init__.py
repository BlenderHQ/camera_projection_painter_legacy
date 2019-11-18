# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

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
    return
    importlib.reload(bl_ui)
    bl_ui.register()
