from .. import engine
from . import utils

if "bpy" in locals():
    import importlib
    importlib.reload(utils)

import bpy


class CPP_OT_refresh_image_preview(bpy.types.Operator):
    bl_idname = "cpp.refresh_image_preview"
    bl_label = "Refresh Previews"
    bl_options = {'INTERNAL'}

    __slots__ = ("timer", "progress")

    images_per_step: bpy.props.IntProperty(
        default=10, min=1, max=1000
    )

    skip_already_set: bpy.props.BoolProperty(default=True)

    def invoke(self, context, event):
        wm = context.window_manager

        steps_count = 1
        image_count = len(bpy.data.images)
        if image_count > self.images_per_step:
            steps_count = int(image_count / self.images_per_step) + 1

        print("images_per_step", steps_count)

        self.progress = utils.progress.invoke_progress(context, steps_count)
        self.progress.ui_cancel_button = 'ESC'
        self.progress.text = f"Update Image Previews ({image_count} images)"
        self.progress.icon = 'IMAGE'
        self.progress.skip_tics = 0

        wm.modal_handler_add(self)
        self.timer = wm.event_timer_add(time_step=1 / 60, window=context.window)

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self.timer)
        utils.progress.end_progress(context, self.progress)
        context.window.cursor_modal_restore()

    def modal(self, context, event):
        if event.type == 'ESC' and event.value == 'PRESS':
            self.cancel(context)
            return {'CANCELLED'}

        elif event.type != 'TIMER':
            return {'RUNNING_MODAL'}

        context.window.cursor_modal_set('WAIT')
        pstep = utils.progress.modal_progress(context, self.progress)

        if pstep == -1:
            return {'RUNNING_MODAL'}

        elif pstep == -2:
            self.cancel(context)
            return {'FINISHED'}

        image_count = len(bpy.data.images)
        start_index = self.images_per_step * self.progress.step
        end_index = start_index + self.images_per_step - 1
        if self.progress.step == self.progress.steps_count - 1:
            end_index = image_count - 1

        print(self.progress.index, start_index, end_index, self.timer.time_delta)

        #engine.updateImageSeqPreviews(bpy.data.images[start_index:end_index], self.skip_already_set, False)
        self.progress.step += 1

        return {'RUNNING_MODAL'}
