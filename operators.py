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
from bpy.props import BoolProperty, EnumProperty

from .gizmos import generate_preview_bincodes
from .utils import (
    utils_state,
    utils_camera,
    utils_base,
    utils_poll,
    utils_draw)

TIME_STEP = 0.01


class CPP_OT_camera_projection_painter(Operator):
    bl_idname = "cpp.camera_projection_painter"
    bl_label = "Camera Projection Painter"

    def __init__(self):
        self.draw_handler = None
        self.mesh_batch = None
        self.image_batch = None
        self.brush_texture_bindcode = None
        self.check_brush_curve_tuple = None
        self.clone_image = None
        self.mouse_position = (0, 0)
        self.draw_preview = True
        self.cleanup_required = None

    def invoke(self, context, event):
        utils_state.state.operator = self

        if utils_poll.tool_setup_poll(context):
            generate_preview_bincodes(self, context)

        wm = context.window_manager
        wm.event_timer_add(time_step = TIME_STEP, window = context.window)
        wm.event_timer_add(time_step = 0.25, window = context.window)
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

        ob = context.image_paint_object
        camera = scene.camera

        self.mouse_position = event.mouse_x, event.mouse_y
        utils_draw.gen_brush_texture(self, context)
        utils_draw.gen_mesh_batch(self, context)

        if scene.cpp.use_auto_set_camera:
            utils_camera.set_camera_by_view(context, self.mouse_position)

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

        image_paint.clone_image = image_paint.clone_image  # TODO: Find a better way to update viewport

        return {'PASS_THROUGH'}


class CPP_OT_bind_camera_image(Operator):
    bl_idname = "cpp.bind_camera_image"
    bl_label = "Bind Image By Name"
    bl_description = "Find image with equal name to camera name.\n" \
                     "If no image packed into .blend, search in Source Images path. (See Scene tab)"
    bl_options = {'REGISTER', 'UNDO'}

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

        if utils_poll.tool_setup_poll(context):
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
        utils_camera.set_camera_by_view(context, utils_state.state.operator.mouse_position)
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


_classes = [
    CPP_OT_camera_projection_painter,
    CPP_OT_bind_camera_image,
    CPP_OT_set_camera_by_view,
    CPP_OT_set_camera_active,
]
register, unregister = bpy.utils.register_classes_factory(_classes)
