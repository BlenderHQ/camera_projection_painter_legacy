# <pep8 compliant>


if "bpy" in locals():  # In case of module reloading
    import types
    import importlib

    _modules = (
        "basis",
        "bind_camera_image",
        "bind_history_remove",
        "call_pie",
        "canvas_to_diffuse",
        "enter_context",
        "free_memory",
        "image_paint",
        "info",
        "set_tmp_camera_active",
        "set_camera_by_view",
        "toggle_camera_usage",
    )

    dict_locals = locals().copy()

    for item_name, item in dict_locals.items():
        if item_name in _modules and isinstance(item, types.ModuleType):
            importlib.reload(item)

    del types
    del importlib
else:
    from . import basis
    from . import bind_camera_image
    from . import bind_history_remove
    from . import call_pie
    from . import canvas_to_diffuse
    from . import enter_context
    from . import free_memory
    from . import image_paint
    from . import info
    from . import set_tmp_camera_active
    from . import set_camera_by_view
    from . import toggle_camera_usage

import bpy

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
CPP_OT_free_memory = free_memory.CPP_OT_free_memory
CPP_OT_bind_history_remove = bind_history_remove.CPP_OT_bind_history_remove
CPP_OT_toggle_camera_usage = toggle_camera_usage.CPP_OT_toggle_camera_usage

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
    CPP_OT_free_memory,
    CPP_OT_bind_history_remove,
    CPP_OT_toggle_camera_usage
]
CPP_OT_toggle_camera_usage

register, unregister = bpy.utils.register_classes_factory(_classes)
