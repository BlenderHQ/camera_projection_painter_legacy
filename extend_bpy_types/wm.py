import os

if "bpy" in locals():
    bpy.types.STATUSBAR_HT_header.draw = original_status_bar_draw
else:
    import bpy
    original_status_bar_draw = bpy.types.STATUSBAR_HT_header.draw


import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty,
    IntProperty,
    IntVectorProperty,
    EnumProperty,
    PointerProperty,
    StringProperty
)



def _restore(wm):
    bpy.types.STATUSBAR_HT_header.draw = original_status_bar_draw
    wm.cpp_progress_seq.clear()


def progress_draw(self, context):  # TODO: Move to ui.py
    layout = self.layout
    layout.use_property_split = True
    layout.use_property_decorate = False
    wm = context.window_manager

    progress_ui_cancel_button = ""
    for progress in wm.cpp_progress_seq:
        progress_ui_cancel_button = progress.ui_cancel_button

    if progress_ui_cancel_button:
        layout.label(text="Cancel", icon=f"EVENT_{progress_ui_cancel_button}")

    layout.separator_spacer()
    for progress in wm.cpp_progress_seq:
        row = layout.row(align=True)
        row.label(text=progress.text, icon=progress.icon)
        srow = row.row(align=True)
        srow.enabled = True
        srow.ui_units_x = 6
        srow.prop(progress, "value", text="")

    layout.separator_spacer()
    scene = context.scene
    view_layer = context.view_layer
    layout.label(text=scene.statistics(view_layer), translate=False)


class ProgressItem(PropertyGroup):
    steps_count: IntProperty(default=1, min=0)

    def _step_update(self, context):
        if self.step > self.steps_count:
            self.step = self.steps_count

    step: IntProperty(default=0, min=0, update=_step_update)

    skip_ticks: IntProperty()
    tic: IntProperty()

    def _get_value(self):
        return int(100 * self.step / self.steps_count)

    value: IntProperty(
        name="Progress",
        default=0, min=0, max=100,
        subtype='PERCENTAGE',
        get=_get_value
    )
    text: StringProperty(default="Progress")
    icon: StringProperty(default='NONE')
    ui_cancel_button: StringProperty(default='')


class WindowManagerProperties(PropertyGroup):
    running: BoolProperty(default=False)
    suspended: BoolProperty(default=False)
    mouse_pos: IntVectorProperty(size=2, default=(0, 0))
    current_selected_camera_ob: PointerProperty(type=bpy.types.Object)

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

    def invoke_progress(self, context, steps_count=1, step=0):
        assert steps_count > 0
        assert steps_count > step >= 0
        wm = self.id_data

        progress_item = wm.cpp_progress_seq.add()
        progress_item.steps_count = steps_count
        progress_item.step = step

        bpy.types.STATUSBAR_HT_header.draw = progress_draw

        return progress_item
