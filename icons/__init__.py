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

import os
import bpy

if "_pcoll" not in locals():
    from bpy.utils import previews
    _pcoll = previews.new()
    del previews


def get_icon_id(key):
    if key not in _pcoll:
        path = os.path.join(os.path.dirname(__file__), "%s.png" % key)
        _pcoll.load(key, path, "IMAGE")
    return _pcoll[key].icon_id


def register():
    pass


def unregister():
    bpy.utils.previews.remove(_pcoll)
