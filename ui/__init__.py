if "bpy" in locals():
    import importlib

    importlib.reload(camera)
    importlib.reload(context_menu)
    importlib.reload(image_paint)
    importlib.reload(scene)
    importlib.reload(template)

    del importlib
else:
    from . import camera
    from . import context_menu
    from . import image_paint
    from . import scene
    from . import template

import bpy

_classes = [
    # ui
    camera.CPP_PT_active_camera_options,
    # ui.camera.CPP_PT_active_camera_calibration,
    # ui.camera.CPP_PT_active_camera_lens_distortion,

    scene.CPP_PT_camera_painter_scene,
    scene.CPP_PT_enter_context,
    #scene.CPP_PT_material_setup,
    #scene.CPP_PT_canvas_setup,

    image_paint.CPP_PT_camera_painter,

    image_paint.CPP_PT_view_options,
    image_paint.CPP_PT_camera_options,
    image_paint.CPP_PT_view_projection_options,
    image_paint.CPP_PT_current_image_preview_options,

    image_paint.CPP_PT_operator_options,
    image_paint.CPP_PT_material_options,
    image_paint.CPP_PT_camera_autocam_options,
    image_paint.CPP_PT_warnings_options,
    image_paint.CPP_PT_memory_options,
    image_paint.CPP_PT_current_camera,
    # image_paint.CPP_PT_current_camera_calibration,
    # image_paint.CPP_PT_current_camera_lens_distortion,

    context_menu.CPP_MT_camera_pie
]
register, unregister = bpy.utils.register_classes_factory(_classes)
