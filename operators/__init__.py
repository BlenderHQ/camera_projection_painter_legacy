# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(camera_projection_painter)
    importlib.reload(bind_camera_image)
    importlib.reload(bind_history_remove)
    importlib.reload(call_pie)
    importlib.reload(canvas_to_diffuse)
    importlib.reload(enter_context)
    importlib.reload(free_memory)
    importlib.reload(image_paint)
    importlib.reload(info)
    importlib.reload(set_camera_active)
    importlib.reload(set_camera_by_view)

    del importlib
else:
    from . import camera_projection_painter
    from . import bind_camera_image
    from . import bind_history_remove
    from . import call_pie
    from . import canvas_to_diffuse
    from . import enter_context
    from . import free_memory
    from . import image_paint
    from . import info
    from . import set_camera_active
    from . import set_camera_by_view

import bpy

CPP_OT_listener = camera_projection_painter.CPP_OT_listener
CPP_OT_camera_projection_painter = camera_projection_painter.CPP_OT_camera_projection_painter
CPP_OT_image_paint = image_paint.CPP_OT_image_paint
CPP_OT_bind_camera_image = bind_camera_image.CPP_OT_bind_camera_image
CPP_OT_set_camera_by_view = set_camera_by_view.CPP_OT_set_camera_by_view
CPP_OT_set_camera_active = set_camera_active.CPP_OT_set_camera_active
CPP_OT_enter_context = enter_context.CPP_OT_enter_context
CPP_OT_canvas_to_diffuse = canvas_to_diffuse.CPP_OT_canvas_to_diffuse
CPP_OT_call_pie = call_pie.CPP_OT_call_pie
CPP_OT_free_memory = free_memory.CPP_OT_free_memory
CPP_OT_bind_history_remove = bind_history_remove.CPP_OT_bind_history_remove

_classes = [
    camera_projection_painter.CPP_OT_listener,
    camera_projection_painter.CPP_OT_camera_projection_painter,
    image_paint.CPP_OT_image_paint,
    bind_camera_image.CPP_OT_bind_camera_image,
    set_camera_by_view.CPP_OT_set_camera_by_view,
    set_camera_active.CPP_OT_set_camera_active,
    enter_context.CPP_OT_enter_context,
    canvas_to_diffuse.CPP_OT_canvas_to_diffuse,
    call_pie.CPP_OT_call_pie,
    free_memory.CPP_OT_free_memory,
    bind_history_remove.CPP_OT_bind_history_remove,
]

register, unregister = bpy.utils.register_classes_factory(_classes)
