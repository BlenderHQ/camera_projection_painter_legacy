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
from bpy.types import Operator
from bpy.props import EnumProperty

from .gizmos import generate_preview_bincodes
from .utils import (
    common,
    utils_state,
    utils_camera,
    utils_base,
    utils_poll,
    utils_draw,
    utils_warning)

import os
import csv

TIME_STEP = 1 / 24


class CPP_OT_event_listener(Operator):
    bl_idname = "cpp.event_listener"
    bl_label = "Event Listener"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        utils_state.event.mouse_position = event.mouse_x, event.mouse_y
        return {'PASS_THROUGH'}


class CPP_OT_image_paint(Operator):
    bl_idname = "cpp.image_paint"
    bl_label = "Image Paint"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if not scene.cpp.use_warnings:
            return False
        return utils_poll.full_poll(context)

    def execute(self, context):
        scene = context.scene
        wm = context.window_manager
        # Danger zone
        rv3d = common.get_hovered_region_3d(context)
        if rv3d:
            warning_status = utils_warning.get_warning_status(context, rv3d)
            if warning_status:
                self.report(type = {'WARNING'}, message = "Danger zone!")
                if scene.cpp.use_warning_action_popup:
                    wm.popup_menu(utils_warning.danger_zone_popup_menu, title = "Danger zone", icon = 'INFO')
                if scene.cpp.use_warning_action_lock:
                    return {'FINISHED'}
        bpy.ops.paint.image_paint('INVOKE_DEFAULT')
        return {'FINISHED'}


class CPP_OT_camera_projection_painter(Operator):
    bl_idname = "cpp.camera_projection_painter"
    bl_label = "Camera Projection Painter"
    bl_options = {'INTERNAL'}

    __slots__ = (
        "draw_handler",
        "mesh_batch",
        "image_batch",
        "brush_texture_bindcode",
        "check_brush_curve_tuple",
        "clone_image",
        "suspended",
        "cleanup_required"
    )

    def __init__(self):
        self.draw_handler = None
        self.mesh_batch = None
        self.image_batch = None
        self.brush_texture_bindcode = None
        self.check_brush_curve_tuple = None
        self.clone_image = None
        self.suspended = True
        self.cleanup_required = False

    def invoke(self, context, event):
        utils_state.state.operator = self

        if utils_poll.tool_setup_poll(context):
            generate_preview_bincodes(self, context)

        wm = context.window_manager
        wm.event_timer_add(time_step = TIME_STEP, window = context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        if utils_poll.base_poll(context):
            self.cleanup_required = True
            utils_base.cleanup(self, context)

    def modal(self, context, event):
        scene = context.scene
        image_paint = scene.tool_settings.image_paint
        if utils_poll.tool_setup_poll(context):
            if not image_paint.clone_image:
                if scene.cpp.use_auto_set_image:
                    utils_base.auto_set_image(context)
                return {'PASS_THROUGH'}
        else:
            utils_base.cleanup(self, context)
            return {'PASS_THROUGH'}

        if not self.cleanup_required:
            generate_preview_bincodes(self, context)

        image_paint.clone_image = image_paint.clone_image  # TODO: Find a better way to update viewport

        if self.suspended:
            return {'PASS_THROUGH'}

        ob = context.image_paint_object
        camera = scene.camera

        utils_draw.gen_brush_texture(self, context)
        utils_draw.gen_mesh_batch(self, context)

        if scene.cpp.use_auto_set_camera:
            utils_camera.set_camera_by_view(context)

        if scene.cpp.use_auto_set_image:
            utils_base.auto_set_image(context)

        modifier = utils_base.set_modifier(ob, state = True)

        if modifier.projectors[0].object != camera:
            modifier.projectors[0].object = camera
            utils_draw.base_update_preview(context)

        if image_paint.clone_image != self.clone_image:
            self.clone_image = image_paint.clone_image

            self.clone_image.colorspace_settings.name = 'Raw'

            size_x, size_y = self.clone_image.size
            # Modifier aspect
            modifier_aspect = (size_x / size_y, 1.0) if size_x > size_y else (1.0, size_x / size_y)
            modifier.aspect_x, modifier.aspect_y = modifier_aspect
            # Scene resolution for background images
            scene.render.resolution_x = size_x
            scene.render.resolution_y = size_y

            utils_draw.base_update_preview(context)

        self.cleanup_required = True

        if not self.draw_handler:
            utils_base.set_draw_handlers(self, context, state = True)

        return {'PASS_THROUGH'}


class CPP_OT_bind_camera_image(Operator):
    bl_idname = "cpp.bind_camera_image"
    bl_label = "Bind Image By Name"
    bl_description = "Find image with equal name to camera name.\n" \
                     "If no image packed into .blend, search in Source Images path. (See Scene tab)"
    bl_options = {'REGISTER'}

    mode: EnumProperty(
        items = [('ACTIVE', "Active", ""),
                 ('SELECTED', "Selected", ""),
                 ('ALL', "All", ""),
                 ('TMP', "Tmp", "")],
        name = "Mode",
        default = 'ACTIVE')

    def execute(self, context):
        scene = context.scene
        file_path = scene.cpp.source_images_path

        cameras = []
        if self.mode == 'ACTIVE':
            cameras = [context.active_object]
        elif self.mode == 'SELECTED':
            cameras = scene.cpp.selected_camera_objects
        elif self.mode == 'ALL':
            cameras = scene.cpp.visible_camera_objects
        elif self.mode == 'TMP':
            cam = utils_state.state.tmp_camera
            if cam:
                cameras = [cam]
        count = 0
        for ob in cameras:
            res = utils_camera.bind_camera_image_by_name(ob, file_path)
            if res:
                count += 1
                print(res)  # Also print list of successfully binded cameras to console

        if count:
            mess = "Binded %d camera images" % count
            if count == 1:
                mess = "Binded %s camera image" % res
            self.report(type = {'INFO'}, message = mess)
        else:
            self.report(type = {'WARNING'}, message = "Images not found!")

        generate_preview_bincodes(self, context)

        return {'FINISHED'}


class CPP_OT_set_camera_by_view(Operator):
    bl_idname = "cpp.set_camera_by_view"
    bl_label = "Set camera by view"
    bl_description = "Automatically select camera as active projector using selected method"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        scene = context.scene
        return scene.cpp.has_available_camera_objects

    def execute(self, context):
        utils_camera.set_camera_by_view(context)
        return {'FINISHED'}


class CPP_OT_set_camera_active(Operator):
    bl_idname = "cpp.set_camera_active"
    bl_label = "Set Active"
    bl_description = "Set camera as active projector"

    @classmethod
    def poll(cls, context):
        if context.scene.camera == utils_state.state.tmp_camera:
            return False
        return True

    def execute(self, context):
        scene = context.scene
        scene.camera = utils_state.state.tmp_camera
        for camera in scene.cpp.visible_camera_objects:
            if camera == scene.camera:
                continue
            camera.select_set(False)
        scene.camera.select_set(True)
        self.report(type = {'INFO'}, message = "%s set active" % scene.camera.name)
        return {'FINISHED'}


class CPP_OT_set_camera_calibration_from_file(Operator):
    bl_idname = "cpp.set_camera_calibration_from_file"
    bl_label = "Set Calibration Parameters"
    bl_description = "Set cameras calibration parameters from file"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        file_path = scene.cpp.calibration_source_file
        if file_path:
            path = bpy.path.abspath(file_path)
            if os.path.isfile(path):
                name, ext = os.path.splitext(path)
                if ext in ('.csv',):
                    return True
        return False

    def execute(self, context):
        scene = context.scene
        file_path = bpy.path.abspath(scene.cpp.calibration_source_file)

        count = 0

        with open(file_path) as file:
            csv_reader = csv.reader(file, delimiter = ',')

            for line in csv_reader:
                if line[0][0] in ('#',):
                    continue
                csv_name = line[0]
                x, y, alt, heading, pitch, roll, f, px, py, k1, k2, k3, k4, t1, t2 = (float(n) for n in line[1:])

                name, ext = os.path.splitext(csv_name)
                for ob in scene.cpp.visible_camera_objects:
                    ob_name, ob_ext = os.path.splitext(ob.name)

                    if name == ob_name:
                        count += 1
                        camera = ob.data
                        camera.cpp.use_calibration = True
                        camera.lens_unit = 'MILLIMETERS'
                        camera.lens = float(f)
                        camera.cpp.calibration_principal_point = (px, py)
                        # camera.cpp.calibration_skew = float()
                        # camera.cpp.calibration_aspect_ratio = float()
                        camera.cpp.lens_distortion_radial_1 = k2
                        camera.cpp.lens_distortion_radial_2 = k3
                        camera.cpp.lens_distortion_radial_3 = k4
                        camera.cpp.lens_distortion_tangential_1 = t1
                        camera.cpp.lens_distortion_tangential_2 = t2

        if count:
            self.report(type = {'INFO'}, message = "Calibrated %d cameras" % count)
        else:
            self.report(type = {'WARNING'}, message = "No data in file for calibration")

        return {'FINISHED'}


_classes = [
    CPP_OT_event_listener,
    CPP_OT_image_paint,
    CPP_OT_camera_projection_painter,
    CPP_OT_bind_camera_image,
    CPP_OT_set_camera_by_view,
    CPP_OT_set_camera_active,
    CPP_OT_set_camera_calibration_from_file,
]
register, unregister = bpy.utils.register_classes_factory(_classes)
