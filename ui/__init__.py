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

from .camera import (
    CPP_PT_active_camera_options,
    CPP_PT_active_camera_calibration,
    CPP_PT_active_camera_lens_distortion)
from .scene import (
    CPP_PT_camera_projection_painter,
    CPP_PT_path,
    CPP_PT_scene_cameras)
from .image_paint import (
    CPP_PT_options,
    CPP_PT_scene_options,
    CPP_PT_camera_options,
    CPP_PT_view_options,
    CPP_PT_camera_autocam_options,
    CPP_PT_view_projection_preview_options,
    CPP_PT_current_image_preview_options,
    CPP_PT_warnings_options,
    CPP_PT_current_camera,
    CPP_PT_current_camera_calibration,
    CPP_PT_current_camera_lens_distortion
)
from .context_menu import CPP_MT_camera_pie

__all__ = ["register", "unregister"]

_classes = [
    CPP_PT_active_camera_options,
    CPP_PT_active_camera_calibration,
    CPP_PT_active_camera_lens_distortion,

    CPP_PT_camera_projection_painter,
    CPP_PT_path,
    CPP_PT_scene_cameras,

    CPP_PT_options,
    CPP_PT_scene_options,
    CPP_PT_camera_options,
    CPP_PT_view_options,
    CPP_PT_camera_autocam_options,
    CPP_PT_view_projection_preview_options,
    CPP_PT_current_image_preview_options,
    CPP_PT_warnings_options,
    CPP_PT_current_camera,
    CPP_PT_current_camera_calibration,
    CPP_PT_current_camera_lens_distortion,

    CPP_MT_camera_pie
]

register, unregister = bpy.utils.register_classes_factory(_classes)
