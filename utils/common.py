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

from mathutils import Vector


def fclamp(value: float, min_value: float, max_value: float):
    return max(min(value, max_value), min_value)


def flerp(value0: float, value1: float, factor: float):
    return (value0 * (1.0 - factor)) + (value1 * factor)


def smooth(a: Vector, b: Vector, fac: float):
    return Vector([(a.x * (1.0 - fac)) + (b.x * fac), (a.y * (1.0 - fac)) + (b.y * fac)])


def iter_curve_values(curve_mapping, steps: int):
    curve_mapping.initialize()
    curve = list(curve_mapping.curves)[0]
    clip_min_x = curve_mapping.clip_min_x
    clip_min_y = curve_mapping.clip_min_y
    clip_max_x = curve_mapping.clip_max_x
    clip_max_y = curve_mapping.clip_max_y

    for i in range(steps):
        fac = i / steps
        pos = flerp(clip_min_x, clip_max_x, fac)
        value = curve.evaluate(pos)
        yield fclamp(value, clip_min_y, clip_max_y)


def get_hovered_region_3d(context, mouse_position):
    mouse_x, mouse_y = mouse_position
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            header = next(r for r in area.regions if r.type == 'HEADER')
            tools = next(r for r in area.regions if r.type == 'TOOLS')  # N-panel
            ui = next(r for r in area.regions if r.type == 'UI')  # T-panel

            min_x = area.x + tools.width
            max_x = area.x + area.width - ui.width
            min_y = area.y
            max_y = area.y + area.height

            if header.alignment == 'TOP':
                max_y -= header.height
            elif header.alignment == 'BOTTOM':
                min_y += header.height

            if min_x <= mouse_x < max_x and min_y <= mouse_y < max_y:
                if len(area.spaces.active.region_quadviews) == 0:
                    return area.spaces.active.region_3d
                else:
                    # Not sure quadview support required?
                    pass
