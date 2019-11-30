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
from bpy.props import StringProperty, EnumProperty

from .constants import TIME_STEP
from .utils import (
    common,
    utils_camera,
    utils_base,
    utils_poll,
    utils_draw,
    utils_warning,
    utils_image
)

import os
import csv

#
camera_painter_operator = None

mouse_position = (0, 0)
tmp_camera = None


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
        rv3d = common.get_hovered_region_3d(context, mouse_position)
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

    def __init__(self):
        utils_base.set_properties_defaults(self)

    def invoke(self, context, event):
        global camera_painter_operator
        camera_painter_operator = self

        wm = context.window_manager
        wm.modal_handler_add(self)
        wm.event_timer_add(time_step = TIME_STEP, window = context.window)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        if not self.setup_required:
            scene = context.scene
            utils_draw.remove_draw_handlers(self)
            ob = context.active_object
            utils_base.remove_uv_layer(ob)
            utils_base.set_properties_defaults(self)
            scene.cpp.cameras_hide_set(state = False)

    def modal(self, context, event):
        scene = context.scene
        ob = context.image_paint_object
        image_paint = scene.tool_settings.image_paint
        clone_image = image_paint.clone_image

        if utils_poll.tool_setup_poll(context):
            if not image_paint.clone_image:
                if scene.cpp.use_auto_set_image:
                    utils_base.set_clone_image_from_camera_data(context)
                return {'PASS_THROUGH'}
        else:
            self.cancel(context)
            return {'PASS_THROUGH'}

        image_paint.clone_image = clone_image  # TODO: Find a better way to update

        if self.suspended:
            return {'PASS_THROUGH'}

        if event.type == 'F' and event.value == 'PRESS':
            self.suspended_mouse = True
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.suspended_mouse = False
        if not (self.suspended_mouse or self.suspended):
            global mouse_position
            mouse_position = event.mouse_x, event.mouse_y
            self.mouse_position = mouse_position

        if scene.cpp.use_projection_preview:
            utils_draw.update_brush_texture_bindcode(self, context)

        if scene.cpp.use_auto_set_camera:
            utils_camera.set_camera_by_view(context, mouse_position)

        if scene.cpp.use_auto_set_image:
            utils_base.set_clone_image_from_camera_data(context)

        camera_ob = scene.camera
        camera = camera_ob.data

        if self.setup_required:
            utils_base.setup_basis_uv_layer(context)
            self.bm = utils_base.get_bmesh(context, ob)
            self.mesh_batch = utils_draw.get_bmesh_batch(self.bm)
            self.camera_batches = utils_draw.get_camera_batches(context)
            utils_draw.add_draw_handlers(self, context)

            scene.cpp.cameras_hide_set(state = True)

        if event.type not in ('TIMER', 'TIMER_REPORT'):
            if self.data_updated((
                    camera_ob, clone_image,  # Base properties

                    camera.lens,
                    camera.cpp.use_calibration,  # Calibration properties
                    camera.cpp.calibration_principal_point[:],
                    camera.cpp.calibration_skew,
                    camera.cpp.calibration_aspect_ratio,
                    camera.cpp.lens_distortion_radial_1,
                    camera.cpp.lens_distortion_radial_2,
                    camera.cpp.lens_distortion_radial_3,
                    camera.cpp.lens_distortion_tangential_1,
                    camera.cpp.lens_distortion_tangential_2,
            )):
                utils_base.setup_basis_uv_layer(context)
                if scene.camera.data.cpp.use_calibration:
                    utils_base.deform_uv_layer(self, context)

                self.camera_batches[camera_ob] = utils_draw.gen_camera_batch(camera)
                utils_draw.base_update_preview(context)

        self.setup_required = False

        return {'PASS_THROUGH'}


class CPP_OT_bind_camera_image(Operator):
    bl_idname = "cpp.bind_camera_image"
    bl_label = "Bind Image By Name"
    bl_description = "Find image with equal name to camera name.\n" \
                     "If no image packed into .blend, search in Source Images path. (See Scene tab)"
    bl_options = {'REGISTER'}

    mode: EnumProperty(
        items = [('ACTIVE', "Active", ""),
                 ('CONTEXT', "Context", ""),
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
        elif self.mode == 'CONTEXT':
            cameras = [scene.camera]
        elif self.mode == 'SELECTED':
            cameras = scene.cpp.selected_camera_objects
        elif self.mode == 'ALL':
            cameras = scene.cpp.camera_objects
        elif self.mode == 'TMP':
            cam = tmp_camera
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
        utils_camera.set_camera_by_view(context, mouse_position)
        return {'FINISHED'}


class CPP_OT_set_camera_active(Operator):
    bl_idname = "cpp.set_camera_active"
    bl_label = "Set Active"
    bl_description = "Set camera as active projector"

    @classmethod
    def poll(cls, context):
        if context.scene.camera == tmp_camera:
            return False
        return True

    def execute(self, context):
        scene = context.scene
        scene.camera = tmp_camera
        for camera in scene.cpp.camera_objects:
            if camera == scene.camera:
                continue
            camera.select_set(False)
        scene.camera.select_set(True)
        if scene.cpp.use_auto_set_image:
            utils_base.set_clone_image_from_camera_data(context)
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
                for ob in scene.cpp.camera_objects:
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


class CPP_OT_enter_context(Operator):
    bl_idname = "cpp.enter_context"
    bl_label = "Setup Context"
    bl_description = "Setup context to begin"

    @classmethod
    def poll(cls, context):
        if utils_poll.full_poll(context):
            return False
        ob = context.active_object
        scene = context.scene
        if ob:
            if ob.type == 'MESH':
                if scene.cpp.has_camera_objects:
                    return True
        return False

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "image_size")

    def execute(self, context):
        ob = context.active_object
        scene = context.scene

        bpy.ops.object.mode_set(mode = 'TEXTURE_PAINT')
        bpy.ops.wm.tool_set_by_id(name = "builtin_brush.Clone", cycle = False, space_type = 'VIEW_3D')

        image_paint = scene.tool_settings.image_paint

        image_paint.use_clone_layer = True
        image_paint.mode = 'IMAGE'
        scene.cpp.mapping = 'CAMERA'

        if image_paint.missing_uvs:
            bpy.ops.object.mode_set(mode = 'EDIT')
            ob.data.uv_layers.new(do_init = True)
            bpy.ops.uv.unwrap(method = 'ANGLE_BASED', margin = 0.001)
            bpy.ops.object.mode_set(mode = 'TEXTURE_PAINT')

        if image_paint.missing_texture:
            name = "%s_Diffuse" % ob.name
            if name not in bpy.data.images:
                bpy.ops.image.new(
                    name = name, width = 2048, height = 2048,
                    generated_type = 'COLOR_GRID')
            image_paint.canvas = bpy.data.images[name]

        return {'FINISHED'}


class CPP_OT_call_pie(Operator):
    bl_idname = "cpp.call_pie"
    bl_label = "CPP Call Pie"
    bl_description = "Open Context Menu"
    bl_options = {'INTERNAL'}

    camera_name: StringProperty()

    @classmethod
    def description(self, context, properties):
        text = "Camera: %s" % properties["camera_name"]
        return text

    def execute(self, context):
        global tmp_camera
        tmp_camera = context.scene.objects[self.camera_name]
        bpy.ops.wm.call_menu_pie(name = "CPP_MT_camera_pie")
        return {'FINISHED'}


class CPP_OT_generate_image_previews(Operator):
    bl_idname = "cpp.generate_image_previews"
    bl_label = "Generate Image Previews"
    bl_description = "Generate image previews to display in UI and viewport"
    bl_options = {'INTERNAL'}

    def set_progress(self, context, value):
        text = "Rendering Previews Progress: %d %%" % value
        context.workspace.status_text_set(text)

    def invoke(self, context, event):
        self.images = bpy.data.images[:]
        li = len(self.images)
        if not li:
            return {'CANCELLED'}
        bpy.ops.wm.previews_clear(id_type = {'IMAGE'})
        utils_draw.clear_preview_bindcodes()

        context.window.cursor_set('WAIT')
        self.set_progress(context, 0.0)
        camera_painter_operator.suspended = True

        wm = context.window_manager
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == "ESC":
            context.window.cursor_set('DEFAULT')
            context.workspace.status_text_set(None)
            camera_painter_operator.suspended = False
            return {'CANCELLED'}
        if not len(self.images):
            self.report(type = {'INFO'}, message = "Image previews generated")
            context.window.cursor_set('DEFAULT')
            context.workspace.status_text_set(None)
            camera_painter_operator.suspended = False
            return {'FINISHED'}

        image = self.images[-1]
        utils_image.generate_preview(image)
        self.images.pop()

        progress = (1.0 - len(self.images) / len(bpy.data.images[:])) * 100
        self.set_progress(context, progress)

        return {'RUNNING_MODAL'}


_classes = [
    CPP_OT_image_paint,
    CPP_OT_camera_projection_painter,
    CPP_OT_bind_camera_image,
    CPP_OT_set_camera_by_view,
    CPP_OT_set_camera_active,
    CPP_OT_set_camera_calibration_from_file,
    CPP_OT_enter_context,
    CPP_OT_call_pie,
    CPP_OT_generate_image_previews,
]
register, unregister = bpy.utils.register_classes_factory(_classes)
