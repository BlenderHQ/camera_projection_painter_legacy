from . import draw
from ... import poll
from ... import extend_bpy_types
from ... import engine
from ... import __package__ as addon_pkg

if "bpy" in locals():
    import importlib
    importlib.reload(draw)
    importlib.reload(poll)
    importlib.reload(extend_bpy_types)
    for operator in modal_ops:
        try:
            operator.cancel(bpy.context)
        except AttributeError:
            print("AttributeError. Missing cancel method", operator)
        except ReferenceError:
            import traceback
            print(traceback.format_exc())

import bpy

modal_ops = []
LISTEN_TIME_STEP = 1 / 4
TIME_STEP = 1 / 60


class PropertyTracker(object):
    __slots__ = ("value",)

    def __init__(self, value=None):
        self.value = value

    def __call__(self, value=None):
        if self.value != value:
            self.value = value
            return True
        return False


class CPP_OT_listener(bpy.types.Operator):
    bl_idname = "cpp.listener"
    bl_label = "Listener"
    bl_options = {'INTERNAL'}

    __slots__ = ("timer", )

    def invoke(self, context, event):
        if self not in modal_ops:
            modal_ops.append(self)

        engine.updateImageSeqStaticSize(bpy.data.images, False)

        wm = context.window_manager
        self.timer = wm.event_timer_add(time_step=LISTEN_TIME_STEP, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        if self in modal_ops:
            modal_ops.remove(self)
        context.window_manager.event_timer_remove(self.timer)

    def modal(self, context, event):
        wm = context.window_manager
        if wm.cpp.running:
            self.cancel(context)
            return {'FINISHED'}
        if event.type == 'TIMER' and (not wm.cpp.running) and (poll.full_poll(context)):
            wm.cpp.running = True
            wm.cpp.suspended = False
            bpy.ops.cpp.camera_projection_painter('INVOKE_DEFAULT')
        engine.updateImageSeqStaticSize(bpy.data.images, skip_already_set=True)
        return {'PASS_THROUGH'}


class CPP_OT_camera_projection_painter(bpy.types.Operator):
    bl_idname = "cpp.camera_projection_painter"
    bl_label = "Camera Projection Painter"
    bl_options = {'INTERNAL'}

    __slots__ = (
        "environment",
        "timer",
        "suspended",
        "suspended_mouse",
        "suspended_brush",
        "paint_time",
        "paint_step",

        "full_draw",
        "draw_handler",
        "draw_handler_cameras",
        "mesh_batch",
        "axes_batch",
        "camera_batch",
        "image_rect_batch",
        "brush_texture_bindcode",

        "check_data_updated",
        "data_updated",
        "check_brush_curve_updated",
    )

    def set_properties_defaults(self):
        """Set default values at startup and after exit available context"""
        self.environment = None

        self.timer = None
        self.suspended = False
        self.suspended_mouse = False
        self.suspended_brush = False
        self.paint_time = 0.0
        self.paint_step = 0

        self.full_draw = False
        self.draw_handler = None
        self.draw_handler_cameras = None
        self.mesh_batch = None
        self.axes_batch = None
        self.camera_batch = None
        self.image_rect_batch = None
        self.brush_texture_bindcode = 0
        self.check_data_updated = PropertyTracker()
        self.data_updated = PropertyTracker()
        self.check_brush_curve_updated = PropertyTracker()

    @staticmethod
    def ensure_uv_layer(ob):
        uv_layers = ob.data.uv_layers
        if engine.TEMP_DATA_NAME not in uv_layers:
            uv_layers.new(name=engine.TEMP_DATA_NAME, do_init=False)
            uv_layer = uv_layers[engine.TEMP_DATA_NAME]
            uv_layer.active = False
            uv_layer.active_clone = True
        assert engine.TEMP_DATA_NAME in uv_layers
        uv_layer = uv_layers[engine.TEMP_DATA_NAME]

        return uv_layer

    @staticmethod
    def remove_uv_layer(ob):
        if ob and ob.type == 'MESH':
            uv_layers = ob.data.uv_layers
            if engine.TEMP_DATA_NAME in uv_layers:
                uv_layers.remove(uv_layers[engine.TEMP_DATA_NAME])

    def invoke(self, context, event):
        self.set_properties_defaults()

        for camera_object in context.scene.cpp.camera_objects:
            # Hide all camera objects
            camera_object.initial_visible = camera_object in context.visible_objects
            camera_object.hide_set(True)

            # Set the camera sensor relative to the larger side of the binded image
            camera = camera_object.data
            image = camera.cpp.image
            if image and image.cpp.valid:
                w, h = image.cpp.static_size
                if (w > h):
                    camera.sensor_fit = 'HORIZONTAL'
                else:
                    camera.sensor_fit = 'VERTICAL'

        # Active camera must remain visible
        context.scene.camera.initial_visible = True

        ob = context.image_paint_object
        clone_uv_layer = self.ensure_uv_layer(ob)

        # Create an environment for the current object
        self.environment = engine.Environment(ob, clone_uv_layer)

        self.mesh_batch = draw.mesh_preview.get_object_batch(context, ob)
        self.axes_batch = draw.cameras.get_axes_batch()
        self.camera_batch, self.image_rect_batch = draw.cameras.get_camera_batches()
        draw.add_draw_handlers(self, context)

        wm = context.window_manager
        self.timer = wm.event_timer_add(time_step=TIME_STEP, window=context.window)
        wm.modal_handler_add(self)

        # User can press Ctrl+Z after operator start, so flush edits
        bpy.ops.ed.flush_edits()

        if self not in modal_ops:
            modal_ops.append(self)

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        if self in modal_ops:
            modal_ops.remove(self)

        ob = context.active_object
        wm = context.window_manager
        if self.timer is not None:
            wm.event_timer_remove(self.timer)

        extend_bpy_types.image.ImageCache.clear()

        draw.remove_draw_handlers(self)
        self.remove_uv_layer(ob)

        for ob in context.scene.cpp.camera_objects:
            ob.hide_set(not ob.initial_visible)

        wm.cpp.running = False
        wm.cpp.suspended = False

        self.set_properties_defaults()

    def modal(self, context, event):
        preferences = context.preferences.addons[addon_pkg].preferences
        wm = context.window_manager

        if not poll.full_poll(context):
            self.cancel(context)
            bpy.ops.cpp.listener('INVOKE_DEFAULT')
            return {'FINISHED'}

        if wm.cpp.suspended:
            return {'PASS_THROUGH'}

        scene = context.scene
        camera_ob = scene.camera
        camera = camera_ob.data
        image_paint = scene.tool_settings.image_paint
        clone_image = image_paint.clone_image

        engine.updateImageSeqStaticSize(bpy.data.images, skip_already_set=True)

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
            wm.cpp.is_image_paint = False

        if not self.suspended_mouse:
            wm.cpp.mouse_pos = event.mouse_x, event.mouse_y

        image = camera.cpp.image
        if image and clone_image != image and image.cpp.valid:
            image_paint.clone_image = image

        if (scene.cpp.use_projection_preview or (scene.cpp.use_warnings and scene.cpp.use_warning_action_draw)):
            draw.mesh_preview.update_brush_texture_bindcode(self, context)

        if scene.cpp.auto_distance_warning and wm.cpp.is_image_paint:
            paint_steps = 5
            if self.paint_step < paint_steps:
                self.paint_time += self.timer.time_delta
                self.paint_step += 1
            else:
                average_paint_time = self.paint_time / paint_steps
                self.paint_time = 0.0
                self.paint_step = 0

                if average_paint_time > 0.045:  # TODO: Maybe, this value should be in user preferences?
                    scene.cpp.distance_warning -= 0.1
                    self.report(type={'WARNING'},
                                message=f"Safe radius is set to {round(scene.cpp.distance_warning, 1)}")

        check_tuple = (
            camera_ob,
            camera,
            clone_image,  # Base properties

            camera.lens,
            camera.cpp.principal_point_x,
            camera.cpp.principal_point_y,
            camera.cpp.skew,
            camera.cpp.aspect_ratio,
            camera.cpp.principal_point_x,
            camera.cpp.principal_point_y,
            camera.cpp.camera_lens_model,
            camera.cpp.k1,
            camera.cpp.k2,
            camera.cpp.k3,
            camera.cpp.k4,
            camera.cpp.t1,
            camera.cpp.t2,
        )

        if self.check_data_updated(check_tuple):
            self.full_draw = True

            w, h = clone_image.cpp.static_size
            scene.render.resolution_x = w
            scene.render.resolution_y = h
            if (w > h):
                camera.sensor_fit = 'HORIZONTAL'
            else:
                camera.sensor_fit = 'VERTICAL'

        if event.type not in ('TIMER', 'TIMER_REPORT'):
            if self.data_updated(check_tuple):
                self.environment.setProjector(camera_ob, preferences.debug_info)

                self.full_draw = False

        return {'PASS_THROUGH'}
