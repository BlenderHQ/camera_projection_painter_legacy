from .. import ui

if "bpy" in locals():
    import importlib
    importlib.reload(ui)
    bpy.types.STATUSBAR_HT_header.draw = original_status_bar_draw
else:
    import bpy
    original_status_bar_draw = bpy.types.STATUSBAR_HT_header.draw

import os
from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    IntVectorProperty,
    EnumProperty,
    PointerProperty,
    StringProperty
)


class WindowManagerProperties(PropertyGroup):
    running: BoolProperty(default=False)
    suspended: BoolProperty(default=False)
    mouse_pos: IntVectorProperty(size=2, default=(0, 0))
    current_selected_camera_ob: PointerProperty(type=bpy.types.Object)
    is_image_paint: BoolProperty(default=False)

    # Import
    def cpp_import_dir_update(self, context):
        if self.import_dir == "":
            return
        fp = bpy.path.abspath(self.import_dir)
        if os.path.isfile(fp):
            self.import_dir = fp = os.path.dirname(fp)
        if not os.path.isdir(fp):
            self.import_dir = ""

    import_dir: StringProperty(subtype='DIR_PATH', update=cpp_import_dir_update)

    import_state: EnumProperty(
        items=(
            ('FILESELECT', 'FILESELECT', ""),
            ('CANCELLED', 'CANCELLED', ""),
            ('FINISHED', 'FINISHED', "")
        ),
        default='FILESELECT'
    )

    # Progress
    def _get_progress(self):
        if self.p_stages_count:
            return int(100.0 * self.p_stage / self.p_stages_count)
        return 100

    def _progress_stage_update(self, context):
        if self.p_stage > self.p_stages_count:
            self.p_stage = self.p_stages_count

    def _progress_set_defaults(self):
        self.p_stage = 0
        self.p_stages_count = 0
        self.p_wait_duration = 0.0

        self.p_text = ""
        self.p_icon = 'NONE'
        self.p_ui_cancel_button = 'NONE'

        bpy.types.STATUSBAR_HT_header.draw = original_status_bar_draw

    def progress_invoke(self, progress_stages_count=1, text="Progress", icon='NONE', ui_cancel_button=''):
        self._progress_set_defaults()
        self.p_stages_count = progress_stages_count
        self.p_text = text
        self.p_icon = icon
        self.p_ui_cancel_button = ui_cancel_button

        bpy.types.STATUSBAR_HT_header.draw = ui.progress_draw

    def progress_modal(self, timer):
        if self.progress >= 100:
            self._progress_set_defaults()
            return -2

        elif self.p_wait_duration > 0.0:
            self.p_wait_duration -= timer.time_delta
            return -1

        return self.p_stage

    def progress_stage_complete(self):
        self.p_stage += 1

    def progress_wait_before_next_stage(self, duration: float):
        self.p_wait_duration = duration

    def progress_complete(self):
        self._progress_set_defaults()

    progress: IntProperty(
        name="Progress",
        default=0, min=0, max=100,
        subtype='PERCENTAGE',
        get=_get_progress
    )
    p_wait_duration: FloatProperty(default=0.0, min=0.0)
    p_stages_count: IntProperty(default=0, min=0)
    p_stage: IntProperty(default=0, min=0, update=_progress_stage_update)

    p_text: StringProperty(default="Progress")
    p_icon: StringProperty(default='NONE')
    p_ui_cancel_button: StringProperty(default='')
