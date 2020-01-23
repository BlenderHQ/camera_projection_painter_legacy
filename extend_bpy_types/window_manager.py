# <pep8 compliant>

# The module contains WindowManager properties

import bpy

cpp_running = bpy.props.BoolProperty(
    default=False,
    options={'SKIP_SAVE'}
)

cpp_suspended = bpy.props.BoolProperty(
    default=False,
    options={'SKIP_SAVE'}
)

cpp_mouse_pos = bpy.props.IntVectorProperty(
    size=2,
    default=(0, 0),
    options={'SKIP_SAVE'}
)

cpp_current_selected_camera_ob = bpy.props.PointerProperty(
    type=bpy.types.Object,
    options={'SKIP_SAVE'}
)
