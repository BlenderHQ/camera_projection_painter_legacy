if "bpy" in locals():
    bpy.types.STATUSBAR_HT_header.draw = original_status_bar_draw
else:
    import bpy
    original_status_bar_draw = bpy.types.STATUSBAR_HT_header.draw


def _restore(wm):
    bpy.types.STATUSBAR_HT_header.draw = original_status_bar_draw
    wm.cpp_progress_seq.clear()


def progress_draw(self, context):
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


def invoke_progress(context, steps_count=1, step=0):
    assert steps_count > 0
    assert steps_count > step >= 0
    wm = context.window_manager

    index = 0

    for p in wm.cpp_progress_seq:
        index = p.index + 1

    progress_item = wm.cpp_progress_seq.add()
    progress_item.steps_count = steps_count
    progress_item.step = step
    progress_item.index = index

    bpy.types.STATUSBAR_HT_header.draw = progress_draw

    return progress_item


def modal_progress(context, progress) -> int:
    if progress.value >= 100:
        return -2
    elif progress.tic >= progress.skip_ticks:
        progress.tic = 0
        return progress.step
    else:
        progress.tic += 1
    return -1


def end_progress(context, progress):
    wm = context.window_manager
    ri = -1
    for i, p in enumerate(wm.cpp_progress_seq):
        if progress.index == i:
            wm.cpp_progress_seq.remove(i)
            ri = i
    wm = context.window_manager
    if ri != -1:
        for p in wm.cpp_progress_seq:
            if p.index <= ri:
                p.index -= 1
    if not len(wm.cpp_progress_seq):
        _restore(wm)
