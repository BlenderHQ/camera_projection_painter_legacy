# <pep8 compliant>

import importlib

import bpy

from . import basis
from . import bind_camera_image
from . import bind_history_remove
from . import call_pie
from . import canvas_to_diffuse
from . import enter_context
from . import image_paint
from . import info
from . import set_tmp_camera_active
from . import set_camera_by_view
from . import toggle_camera_usage
from . import enable_all_cameras
from . import set_camera_radial
from . import set_sensors
from . import add_workflow_preset


if "_rc" in locals():  # In case of module reloading
    importlib.reload(basis)
    importlib.reload(bind_camera_image)
    importlib.reload(bind_history_remove)
    importlib.reload(call_pie)
    importlib.reload(canvas_to_diffuse)
    importlib.reload(enter_context)
    importlib.reload(image_paint)
    importlib.reload(info)
    importlib.reload(set_tmp_camera_active)
    importlib.reload(set_camera_by_view)
    importlib.reload(toggle_camera_usage)
    importlib.reload(enable_all_cameras)
    importlib.reload(set_camera_radial)
    importlib.reload(set_sensors)
    importlib.reload(add_workflow_preset)

_rc = None


CPP_OT_listener = basis.CPP_OT_listener
CPP_OT_camera_projection_painter = basis.CPP_OT_camera_projection_painter
CPP_OT_image_paint = image_paint.CPP_OT_image_paint
CPP_OT_bind_camera_image = bind_camera_image.CPP_OT_bind_camera_image
CPP_OT_set_camera_by_view = set_camera_by_view.CPP_OT_set_camera_by_view
CPP_OT_set_tmp_camera_active = set_tmp_camera_active.CPP_OT_set_tmp_camera_active
CPP_OT_enter_context = enter_context.CPP_OT_enter_context
CPP_OT_canvas_to_diffuse = canvas_to_diffuse.CPP_OT_canvas_to_diffuse
CPP_OT_call_pie = call_pie.CPP_OT_call_pie
CPP_OT_info = info.CPP_OT_info
CPP_OT_bind_history_remove = bind_history_remove.CPP_OT_bind_history_remove
CPP_OT_toggle_camera_usage = toggle_camera_usage.CPP_OT_toggle_camera_usage
CPP_OT_enable_all_cameras = enable_all_cameras.CPP_OT_enable_all_cameras
CPP_OT_set_camera_radial = set_camera_radial.CPP_OT_set_camera_radial
CPP_OT_set_all_cameras_sensor = set_sensors.CPP_OT_set_all_cameras_sensor
CPP_OT_add_workflow_preset = add_workflow_preset.CPP_OT_add_workflow_preset

_classes = [
    CPP_OT_listener,
    CPP_OT_camera_projection_painter,
    CPP_OT_image_paint,
    CPP_OT_bind_camera_image,
    CPP_OT_set_camera_by_view,
    CPP_OT_set_tmp_camera_active,
    CPP_OT_enter_context,
    CPP_OT_canvas_to_diffuse,
    CPP_OT_call_pie,
    CPP_OT_bind_history_remove,
    CPP_OT_toggle_camera_usage,
    CPP_OT_enable_all_cameras,
    CPP_OT_set_camera_radial,
    CPP_OT_set_all_cameras_sensor,
    CPP_OT_add_workflow_preset,
]

register, unregister = bpy.utils.register_classes_factory(_classes)
