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

bl_info = {
    "name": "Camera Projection Painter",
    "author": "Vlad Kuzmin, Ivan Perevala",
    "version": (0, 1, 1, 8),
    "blender": (2, 80, 0),
    "description": "Expanding capabilities of texture paint Clone Brush",
    "location": "Clone Brush tool settings, Scene tab, Camera tab",
    "warning": "4-th digit in version is just for development. It will be removed in release version",
    "wiki_url": "",
    "support": 'COMMUNITY',
    "category": "Paint",
}

if "bpy" in locals():
    import os
    import importlib

    from . import operators

    operators.camera_painter_operator.cancel(bpy.context)

    unregister()

    for module_name, module_file in sorted(bpy.path.module_names(
            path = os.path.dirname(__file__), recursive = True),
            key = lambda x: x[1]):
        module = importlib.import_module(name = "." + module_name, package = __package__)
        importlib.reload(module)
        del module

    register()

    bpy.ops.cpp.camera_projection_painter('INVOKE_DEFAULT')

    del operators
    del importlib
    del os

else:
    import bpy

    _modules = [
        "locale",
        "icons",
        "extend_bpy_types",
        "keymap",
        "preferences",
        "operators",
        "gizmos",
        "ui",
        "handlers"
    ]

    register, unregister = bpy.utils.register_submodule_factory(module_name = __name__, submodule_names = _modules)
