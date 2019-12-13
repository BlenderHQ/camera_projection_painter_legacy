bl_info = {
    "name": "Camera Projection Painter",
    "author": "Vlad Kuzmin, Ivan Perevala",
    "version": (0, 1, 1, 9),
    "blender": (2, 80, 0),
    "description": "Expanding capabilities of texture paint Clone Brush",
    "location": "Clone Brush tool settings, Scene tab, Camera tab",
    "wiki_url": "",
    "support": 'COMMUNITY',
    "category": "Paint",
}

if "bpy" in locals():
    import importlib

    importlib.reload(icons)
    importlib.reload(shaders)
    importlib.reload(preferences)
    importlib.reload(keymap)
    importlib.reload(extend_bpy_types)
    importlib.reload(utils)
    importlib.reload(ui)
    importlib.reload(overwrite_ui)
    importlib.reload(operators)
    importlib.reload(gizmos)
    importlib.reload(handlers)

    del importlib

else:
    from . import icons
    from . import shaders
    from . import preferences
    from . import keymap
    from . import extend_bpy_types
    from . import utils
    from . import ui
    from . import overwrite_ui
    from . import operators
    from . import gizmos
    from . import handlers

import bpy

_classes = (
    # extend_bpy_types
    extend_bpy_types.CameraProperties,
    extend_bpy_types.SceneProperties,
    extend_bpy_types.ImageProperties,
    # preferences
    preferences.CppPreferences,
    # operators
    operators.CPP_OT_listener,
    operators.CPP_OT_camera_projection_painter,
    operators.CPP_OT_image_paint,
    operators.CPP_OT_bind_camera_image,
    operators.CPP_OT_set_camera_by_view,
    operators.CPP_OT_set_camera_active,
    operators.CPP_OT_set_camera_calibration_from_file,
    operators.CPP_OT_enter_context,
    operators.CPP_OT_call_pie,
    operators.CPP_OT_free_memory,
    # gizmos
    gizmos.CPP_GGT_camera_gizmo_group,
    gizmos.CPP_GT_current_image_preview,
    gizmos.CPP_GGT_image_preview_gizmo_group,
    # ui
    ui.camera.CPP_PT_active_camera_options,
    # ui.camera.CPP_PT_active_camera_calibration,
    # ui.camera.CPP_PT_active_camera_lens_distortion,

    ui.scene.CPP_PT_camera_painter_scene,

    ui.image_paint.CPP_PT_camera_painter,

    ui.image_paint.CPP_PT_view_options,
    ui.image_paint.CPP_PT_camera_options,
    ui.image_paint.CPP_PT_view_projection_options,
    ui.image_paint.CPP_PT_current_image_preview_options,

    ui.image_paint.CPP_PT_operator_options,
    ui.image_paint.CPP_PT_camera_autocam_options,
    ui.image_paint.CPP_PT_warnings_options,
    ui.image_paint.CPP_PT_memory_options,
    ui.image_paint.CPP_PT_current_camera,
    # ui.image_paint.CPP_PT_current_camera_calibration,
    # ui.image_paint.CPP_PT_current_camera_lens_distortion,

    ui.context_menu.CPP_MT_camera_pie
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

    # icons.register()
    keymap.register()
    extend_bpy_types.register()
    overwrite_ui.register()
    handlers.register()


def unregister():
    handlers.unregister()
    keymap.unregister()

    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)

    overwrite_ui.unregister()
    extend_bpy_types.unregister()
    icons.unregister()
