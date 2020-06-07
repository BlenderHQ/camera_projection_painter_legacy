from . import basis
from . import bind_camera_image
from . import bind_history_remove
from . import call_pie
from . import image_paint
from . import set_tmp_camera_active
from . import toggle_camera_usage
from . import enable_all_cameras
from . import import_cameras_csv
from . import import_cameras_xml
from . import enter_context
from . import refresh_image_preview


if "bpy" in locals():
    import importlib
    importlib.reload(basis)
    importlib.reload(bind_camera_image)
    importlib.reload(bind_history_remove)
    importlib.reload(call_pie)
    importlib.reload(image_paint)
    importlib.reload(set_tmp_camera_active)
    importlib.reload(toggle_camera_usage)
    importlib.reload(enable_all_cameras)
    importlib.reload(import_cameras_csv)
    importlib.reload(import_cameras_xml)
    importlib.reload(enter_context)
    importlib.reload(refresh_image_preview)

import bpy


CPP_OT_listener = basis.CPP_OT_listener
CPP_OT_camera_projection_painter = basis.CPP_OT_camera_projection_painter
CPP_OT_image_paint = image_paint.CPP_OT_image_paint
CPP_OT_bind_camera_image = bind_camera_image.CPP_OT_bind_camera_image
CPP_OT_set_tmp_camera_active = set_tmp_camera_active.CPP_OT_set_tmp_camera_active
CPP_OT_call_pie = call_pie.CPP_OT_call_pie
CPP_OT_bind_history_remove = bind_history_remove.CPP_OT_bind_history_remove
CPP_OT_toggle_camera_usage = toggle_camera_usage.CPP_OT_toggle_camera_usage
CPP_OT_enable_all_cameras = enable_all_cameras.CPP_OT_enable_all_cameras
CPP_OT_import_cameras_csv = import_cameras_csv.CPP_OT_import_cameras_csv
CPP_OT_import_cameras_xml = import_cameras_xml.CPP_OT_import_cameras_xml

CPP_OT_io_fbx = enter_context.io_fbx.CPP_OT_io_fbx
CPP_OT_enter_context = enter_context.CPP_OT_enter_context

CPP_OT_refresh_image_preview = refresh_image_preview.CPP_OT_refresh_image_preview

_classes = [
    CPP_OT_listener,
    CPP_OT_camera_projection_painter,
    CPP_OT_image_paint,
    CPP_OT_bind_camera_image,
    CPP_OT_set_tmp_camera_active,
    CPP_OT_call_pie,
    CPP_OT_bind_history_remove,
    CPP_OT_toggle_camera_usage,
    CPP_OT_enable_all_cameras,
    CPP_OT_import_cameras_csv,
    CPP_OT_import_cameras_xml,

    # Enter context
    CPP_OT_io_fbx,
    enter_context.ui_io_fbx.CPP_PT_fbx_import_include,
    enter_context.ui_io_fbx.CPP_PT_fbx_import_transform,
    enter_context.ui_io_fbx.CPP_PT_fbx_import_transform_manual_orientation,
    enter_context.ui_io_fbx.CPP_PT_fbx_import_animation,
    enter_context.ui_io_fbx.CPP_PT_fbx_import_armature,
    CPP_OT_enter_context,

    # Previews
    CPP_OT_refresh_image_preview,
]

register, unregister = bpy.utils.register_classes_factory(_classes)
