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


def get_warning_status(context, rv3d):
    result = False
    if rv3d:
        scene = context.scene
        image_paint = scene.tool_settings.image_paint
        brush_radius = scene.tool_settings.unified_paint_settings.size

        view_distance = rv3d.view_distance
        sx, sy = image_paint.canvas.size
        canvas_size = (sx + sy) / 2
        distance_warning = scene.cpp.distance_warning
        brush_radius_warning = scene.cpp.brush_radius_warning
        canvas_size_warning = scene.cpp.canvas_size_warning
        dist_fac = abs((view_distance / distance_warning))
        brad_fac = (brush_radius / brush_radius_warning) - 1
        canv_fac = (canvas_size / canvas_size_warning) - 1
        warning_factor = (dist_fac + brad_fac + canv_fac)

        if warning_factor > 0.95:
            result = True
    return result


def danger_zone_popup_menu(self, context):
    layout = self.layout

    layout.emboss = 'NONE'

    scene = context.scene

    layout.label(text = "Recommended paint context:")
    layout.separator()
    row = layout.row()

    col = row.column()
    col.label(text = "View Distance:")
    col.label(text = "Brush Radius:")
    col.label(text = "Canvas Size:")

    col = row.column()
    col.emboss = 'NORMAL'
    col.label(text = "%d %s" % (scene.cpp.distance_warning, str(scene.unit_settings.length_unit).capitalize()))
    col.label(text = "%d Pixels" % scene.cpp.brush_radius_warning)
    col.label(text = "%d Pixels" % scene.cpp.canvas_size_warning)
