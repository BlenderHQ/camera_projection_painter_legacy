# <pep8 compliant>


if "bpy" in locals():
    for op in modal_ops:
        if hasattr(op, "cancel"):
            try:
                op.cancel(bpy.context)
            except:
                import traceback

                print(traceback.format_exc())

    import importlib

    importlib.reload(utils)
    importlib.reload(constants)

    del importlib
else:
    from . import utils
    from . import constants

import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty

import os
import csv
import re

modal_ops = []
tmp_camera = None


class CPP_OT_listener(Operator):
    bl_idname = "cpp.listener"
    bl_label = "Listener"
    bl_options = {'INTERNAL'}

    def cancel(self, context):
        if self in modal_ops:
            modal_ops.remove(self)

        wm = context.window_manager
        wm.event_timer_remove(self.timer)

    def invoke(self, context, event):
        if not self in modal_ops:
            modal_ops.append(self)

        wm = context.window_manager
        self.timer = wm.event_timer_add(time_step = constants.LISTEN_TIME_STEP, window = context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        wm = context.window_manager
        if wm.cpp_running:
            self.cancel(context)
            return {'FINISHED'}

        if event.type == 'TIMER':
            if not wm.cpp_running:
                if utils.poll.full_poll(context):
                    wm.cpp_running = True
                    wm.cpp_suspended = False
                    bpy.ops.cpp.camera_projection_painter('INVOKE_DEFAULT')

        return {'PASS_THROUGH'}


class CPP_OT_camera_projection_painter(Operator):
    bl_idname = "cpp.camera_projection_painter"
    bl_label = "Camera Projection Painter"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        if not self in modal_ops:
            modal_ops.append(self)

        utils.base.set_properties_defaults(self)

        scene = context.scene
        ob = context.image_paint_object

        utils.base.setup_basis_uv_layer(context)
        self.bm = utils.base.get_bmesh(context, ob)
        self.mesh_batch = utils.draw.get_bmesh_batch(self.bm)
        self.camera_batches = utils.draw.get_camera_batches(context)
        utils.draw.add_draw_handlers(self, context)
        scene.cpp.cameras_hide_set(state = True)

        wm = context.window_manager
        self.timer = wm.event_timer_add(time_step = constants.TIME_STEP, window = context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        if self in modal_ops:
            modal_ops.remove(self)

        scene = context.scene
        ob = context.active_object
        wm = context.window_manager
        wm.event_timer_remove(self.timer)

        utils.draw.clear_image_previews()
        utils.draw.remove_draw_handlers(self)
        utils.base.remove_uv_layer(ob)
        scene.cpp.cameras_hide_set(state = False)

        wm.cpp_running = False
        wm.cpp_suspended = False

        utils.base.set_properties_defaults(self)

    def modal(self, context, event):
        wm = context.window_manager

        if not utils.poll.full_poll(context):
            self.cancel(context)
            bpy.ops.cpp.listener('INVOKE_DEFAULT')
            return {'FINISHED'}

        if wm.cpp_suspended:
            return {'PASS_THROUGH'}

        scene = context.scene

        # update viewports on mouse movements
        if event.type == 'MOUSEMOVE':
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

        # deal with hotkey adjust brush radius/strength
        if event.type == 'F' and event.value == 'PRESS':
            self.suspended_mouse = True
            self.suspended_brush = False
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.suspended_mouse = False
            self.suspended_brush = True
        elif event.value == 'RELEASE':
            self.suspended_mouse = False
            self.suspended_brush = False

        if not self.suspended_mouse:
            wm.cpp_mouse_pos = event.mouse_x, event.mouse_y

        image_paint = scene.tool_settings.image_paint
        clone_image = image_paint.clone_image

        # Manully call image.buffers_free(). BF does't do this so Blender often crashes
        # Also, it checks if image preview generated
        utils.draw.check_image_previews(context)

        if scene.cpp.use_projection_preview:
            utils.draw.update_brush_texture_bindcode(self, context)

        if scene.cpp.use_auto_set_camera:
            utils.common.set_camera_by_view(context, wm.cpp_mouse_pos)

        if scene.cpp.use_auto_set_image:
            utils.common.set_clone_image_from_camera_data(context)

        camera_ob = scene.camera
        camera = camera_ob.data

        if self.check_camera_frame_updated(camera.view_frame()):
            self.camera_batches[camera_ob] = utils.draw.gen_camera_batch(camera)
            self.full_draw = True

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
                utils.base.setup_basis_uv_layer(context)
                if scene.camera.data.cpp.use_calibration:
                    utils.base.deform_uv_layer(self, context)
                self.full_draw = False

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
        if context.area.type != 'VIEW_3D':
            return False
        return utils.poll.full_poll(context)

    def execute(self, context):
        scene = context.scene
        wm = context.window_manager

        mpos = wm.cpp_mouse_pos
        warning_status = utils.common.get_warning_status(context, mpos)
        if warning_status:
            self.report(type = {'WARNING'}, message = "Danger zone!")
            if scene.cpp.use_warning_action_popup:
                wm.popup_menu(utils.common.danger_zone_popup_menu, title = "Danger zone", icon = 'INFO')
            if scene.cpp.use_warning_action_lock:
                return {'FINISHED'}
        bpy.ops.paint.image_paint('INVOKE_DEFAULT')
        return {'FINISHED'}


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
        source_images_path = bpy.path.native_pathsep(bpy.path.abspath(scene.cpp.source_images_path))

        cameras = []
        if self.mode == 'ACTIVE':
            ob = context.active_object
            cameras = [ob] if ob.type == 'CAMERA' else []
        elif self.mode == 'CONTEXT':
            cameras = [scene.camera]
        elif self.mode == 'SELECTED':
            cameras = scene.cpp.selected_camera_objects
        elif self.mode == 'ALL':
            cameras = scene.cpp.camera_objects
        elif self.mode == 'TMP':
            ob = tmp_camera
            if ob:
                cameras = [ob] if ob.type == 'CAMERA' else []
        count = 0

        file_list = []
        if os.path.isdir(source_images_path):
            file_list = [
                bpy.path.native_pathsep(os.path.join(source_images_path, n)) for n in os.listdir(source_images_path)
            ]

        for ob in cameras:
            res = utils.common.bind_camera_image_by_name(ob, file_list)
            if res:
                count += 1
                # Also print list of successfully binded cameras to console
                print("Camera: %s - Image: %s" % (ob.name, res.name))

        if count:
            mess = "Binded %d camera images" % count
            if count == 1:
                mess = "Binded %s camera image" % res.name
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
        wm = context.window_manager
        utils.common.set_camera_by_view(context, wm.cpp_mouse_pos)
        return {'FINISHED'}


class CPP_OT_set_camera_active(Operator):
    bl_idname = "cpp.set_camera_active"
    bl_label = "Set Active"
    bl_description = "Set camera as active projector"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.camera == tmp_camera:
            return False
        return True

    def execute(self, context):
        scene = context.scene
        if scene.cpp.use_auto_set_camera:
            scene.cpp.use_auto_set_camera = False
        scene.camera = tmp_camera
        for camera in scene.cpp.camera_objects:
            if camera == scene.camera:
                continue
        if scene.cpp.use_auto_set_image:
            utils.common.set_clone_image_from_camera_data(context)
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


class CPP_OT_canvas_to_diffuse(Operator):
    bl_idname = "cpp.canvas_to_diffuse"
    bl_label = "Set Canvas To Diffuse"

    @classmethod
    def description(cls, context, properties):
        if properties.reverse:
            return "Search for a diffuse texture node and set it as a canvas"
        else:
            return "Setting an image in a diffuse texture node with creating missing nodes"

    reverse: bpy.props.BoolProperty(default = False)

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if not ob:
            return False
        return ob.active_material

    def execute(self, context):
        ob = context.active_object
        scene = context.scene
        image_paint = scene.tool_settings.image_paint

        material = ob.active_material

        if self.reverse:
            if not material.use_nodes:
                self.report(type = {'WARNING'}, message = "Material not using nodes!")
                return {'CANCELLED'}

            res = utils.common.set_material_diffuse_to_canvas(image_paint, material)
            if res == -1:
                self.report(type = {'INFO'}, message = "Successfully set Canvas from Diffuse")
            elif res == 1:
                self.report(type = {'WARNING'}, message = "Material have no active output!")
            elif res == 2:
                self.report(type = {'WARNING'}, message = "Found invalid image from nodes!")
            elif res == 3:
                self.report(type = {'WARNING'}, message = "Image not found!")

        else:
            res = utils.common.set_canvas_to_material_diffuse(material, image_paint.canvas)

        return {'FINISHED'}


class CPP_OT_enter_context(Operator):
    bl_idname = "cpp.enter_context"
    bl_label = "Setup Context"

    @classmethod
    def poll(cls, context):
        if utils.poll.full_poll(context):
            return False
        ob = context.active_object
        if not ob:
            return False
        if ob.type != 'MESH':
            return False
        scene = context.scene
        if not scene.cpp.has_camera_objects:
            return True
        return True

    @classmethod
    def description(cls, context, properties):
        ob = context.active_object
        scene = context.scene
        image_paint = scene.tool_settings.image_paint

        res = ""
        _num = 1

        if ob.mode != 'TEXTURE_PAINT':
            res += "%s. Object mode will be changed to Texture Paint" % _num
            res += "\n"
            _num += 1

        tool = context.workspace.tools.from_space_view3d_mode(context.mode, create = False)
        if tool.idname != "builtin_brush.Clone":
            res += "%s. Tool will be set to Clone" % _num
            res += "\n"
            _num += 1

        if image_paint.mode != 'IMAGE':
            res += "%s. Image Paint Mode will be set to Single Image" % _num
            res += "\n"
            _num += 1

        if not image_paint.use_clone_layer:
            res += "%s. Image Paint will Use Clone Layer" % _num
            res += "\n"
            _num += 1

        if scene.cpp.mapping != 'CAMERA':
            res += "%s. Image Paint Mapping will be set to Camera" % _num
            res += "\n"
            _num += 1

        if not scene.cpp.use_auto_set_image:
            res += "%s. Image Paint Auto Set Image will be set to True" % _num
            res += "\n"
            _num += 1

        camera_ob = scene.camera
        if not camera_ob:
            if scene.cpp.has_available_camera_objects:
                camera_ob = list(scene.cpp.available_camera_objects)[0]
                res += "%s. Scene camera will be set to %s" % (_num, camera_ob.name)
                res += "\n"
                _num += 1

        if camera_ob:
            image = camera_ob.data.cpp.image
            if image:
                if not image.cpp.invalid:
                    if image != image_paint.clone_image:
                        res += "%s. Image Paint Clone Image will be set to %s" % (_num, image.name)
                        res += "\n"
                        _num += 1

        if not res:
            res = "Context is ready"

        return res

    def execute(self, context):
        ob = context.active_object
        scene = context.scene
        image_paint = scene.tool_settings.image_paint

        if ob.mode != 'TEXTURE_PAINT':
            bpy.ops.object.mode_set(mode = 'TEXTURE_PAINT')

        tool = context.workspace.tools.from_space_view3d_mode(context.mode, create = False)
        if tool.idname != "builtin_brush.Clone":
            bpy.ops.wm.tool_set_by_id(name = "builtin_brush.Clone", cycle = False, space_type = 'VIEW_3D')

        if image_paint.mode != 'IMAGE':
            image_paint.mode = 'IMAGE'

        if not image_paint.use_clone_layer:
            image_paint.use_clone_layer = True

        if scene.cpp.mapping != 'CAMERA':
            scene.cpp.mapping = 'CAMERA'

        if not scene.cpp.use_auto_set_image:
            scene.cpp.use_auto_set_image = True

        if not scene.camera:
            if scene.cpp.has_available_camera_objects:
                scene.camera = list(scene.cpp.available_camera_objects)[0]

        if scene.camera:
            image = scene.camera.data.cpp.image
            if image:
                if not image.cpp.invalid:
                    image_paint.clone_image = image

        return {'FINISHED'}


class CPP_OT_call_pie(Operator):
    bl_idname = "cpp.call_pie"
    bl_label = "CPP Call Pie"
    bl_options = {'INTERNAL'}

    camera_name: StringProperty()

    @classmethod
    def description(self, context, properties):
        text = "Camera: %s" % properties["camera_name"]
        return text

    def execute(self, context):
        global tmp_camera
        scene = context.scene
        if self.camera_name in scene.objects:
            ob = scene.objects[self.camera_name]
            if ob.type == 'CAMERA':
                tmp_camera = ob
                bpy.ops.wm.call_menu_pie(name = "CPP_MT_camera_pie")
        return {'FINISHED'}


class CPP_OT_free_memory(Operator):
    bl_idname = "cpp.free_memory"
    bl_label = "Free Memory"
    bl_description = "Free unused images from memory"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        if utils.draw.get_loaded_images_count() > 2:
            return True
        return False

    def execute(self, context):
        scene = context.scene
        image_paint = scene.tool_settings.image_paint

        count = 0
        for image in bpy.data.images:
            if image not in (image_paint.canvas, image_paint.clone_image):
                if image.has_data:
                    image.buffers_free()
                    count += 1

        self.report(type = {'INFO'}, message = "Freed %d images" % count)

        return {'FINISHED'}


class CPP_OT_info(Operator):
    bl_idname = "cpp.info"
    bl_label = "Info"

    text: bpy.props.StringProperty(default = "Info")

    @classmethod
    def description(self, context, properties):
        return properties.text

    def draw(self, context):
        layout = self.layout
        layout.emboss = 'NONE'
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align = True)

        lines = (l for l in str(self.text).splitlines() if l)

        icon_list = ['ERROR', 'INFO']

        for line in lines:
            if line.startswith("https://"):
                col.separator()
                col.operator("wm.url_open", text = line, icon = 'URL').url = line
            else:
                splits = line.split('#')
                tag = splits[0]
                if tag in icon_list:
                    text = "".join(splits[1::])
                    col.label(text = text, icon = splits[0])
                elif tag == "WEB":
                    text = "".join(splits[1::])
                    row = col.row()
                    row.emboss = 'NORMAL'
                    row.operator("wm.url_open", text = text, icon = 'URL').url = text
                else:
                    col.label(text = line)

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_popup(self)

    def execute(self, context):
        return {'FINISHED'}


_classes = [
    CPP_OT_listener,
    CPP_OT_camera_projection_painter,
    CPP_OT_image_paint,
    CPP_OT_bind_camera_image,
    CPP_OT_set_camera_by_view,
    CPP_OT_set_camera_active,
    CPP_OT_set_camera_calibration_from_file,
    CPP_OT_enter_context,
    CPP_OT_canvas_to_diffuse,
    CPP_OT_call_pie,
    CPP_OT_free_memory,
]

register, unregister = bpy.utils.register_classes_factory(_classes)
