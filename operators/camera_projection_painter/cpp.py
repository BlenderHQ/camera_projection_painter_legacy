if "bpy" in locals():  # In case of module reloading
    for operator in modal_ops:
        try:
            operator.cancel(bpy.context)
        except:
            import traceback

            print(traceback.format_exc())

    import importlib

    importlib.reload(utils)
    importlib.reload(constants)

    del importlib
else:
    from . import base
    from ... import utils
    from ... import constants

import bpy

modal_ops = []


def listener_cancel(self, context):
    if self in modal_ops:
        modal_ops.remove(self)

    wm = context.window_manager
    wm.event_timer_remove(self.timer)


def listener_invoke(self, context, event):
    if self not in modal_ops:
        modal_ops.append(self)

    wm = context.window_manager
    self.timer = wm.event_timer_add(time_step = constants.LISTEN_TIME_STEP, window = context.window)
    wm.modal_handler_add(self)
    return {'RUNNING_MODAL'}


def listener_modal(self, context, event):
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


def invoke(self, context, event):
    if not self in modal_ops:
        modal_ops.append(self)

    base.set_properties_defaults(self)

    scene = context.scene
    ob = context.image_paint_object

    base.setup_basis_uv_layer(context)
    self.bm = base.get_bmesh(context, ob)
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
    base.remove_uv_layer(ob)
    scene.cpp.cameras_hide_set(state = False)

    wm.cpp_running = False
    wm.cpp_suspended = False

    base.set_properties_defaults(self)


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
            base.setup_basis_uv_layer(context)
            if scene.camera.data.cpp.use_calibration:
                base.deform_uv_layer(self, context)
            self.full_draw = False

    return {'PASS_THROUGH'}
