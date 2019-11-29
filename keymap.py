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

from .operators import CPP_OT_image_paint, CPP_OT_set_camera_by_view

__all__ = ["register", "unregister"]

_keymaps = []


def register():
    wm = bpy.context.window_manager
    # "https://developer.blender.org/T60766"
    kc = wm.keyconfigs.addon

    km = kc.keymaps.new("Image Paint")

    kmi = km.keymap_items.new(
        idname = CPP_OT_image_paint.bl_idname,
        type = 'LEFTMOUSE',
        value = 'PRESS',
        head = True
    )
    _keymaps.append((km, kmi))

    kmi = km.keymap_items.new(CPP_OT_set_camera_by_view.bl_idname, 'X', 'PRESS', alt = True)
    _keymaps.append((km, kmi))

    kmi = km.keymap_items.new("view3d.view_center_pick", 'SPACE', 'PRESS', alt = True)
    _keymaps.append((km, kmi))

    kmi = km.keymap_items.new("wm.context_toggle", 'I', 'PRESS')
    kmi.properties.data_path = "scene.cpp.use_camera_image_previews"
    _keymaps.append((km, kmi))

    kmi = km.keymap_items.new("wm.context_toggle", 'O', 'PRESS')
    kmi.properties.data_path = "scene.cpp.use_projection_preview"
    _keymaps.append((km, kmi))

    kmi = km.keymap_items.new("wm.context_toggle", 'P', 'PRESS')
    kmi.properties.data_path = "scene.cpp.use_current_image_preview"
    _keymaps.append((km, kmi))


def unregister():
    for km, kmi in _keymaps:
        km.keymap_items.remove(kmi)
    _keymaps.clear()
