# <pep8 compliant>

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

    importlib.reload(constants)
    importlib.reload(icons)
    importlib.reload(shaders)
    importlib.reload(preferences)
    importlib.reload(keymap)
    importlib.reload(utils)
    importlib.reload(extend_bpy_types)
    importlib.reload(ui)
    importlib.reload(overwrite_ui)
    importlib.reload(operators)
    importlib.reload(gizmos)

    # \\dev purposes
    # in my opinion I've used my own reloading methods
    # but also you can press ctrl + F8 key to stop modal operators
    # and then reload using bpy.ops.script.reload() using your favorite hotkey
    _reg = False
    _load_post_register(None)
    _load_post_handler(None)
    # //

    del importlib

else:
    from . import constants
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

import bpy
from bpy.app.handlers import persistent

_classes = (
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

    ui.context_menu.CPP_MT_camera_pie,
)

_reg = False


@persistent
def _load_post_register(dummy):
    # all important register functions called only on load_post
    # user should reload file or Blender to start main operators
    # so when user enable an addon, only preferences are registered
    # to show a message about required reloading
    global _reg
    if not _reg:
        _reg = True
        extend_bpy_types.register_types()
        for cls in _classes:
            bpy.utils.register_class(cls)
        keymap.register()
        overwrite_ui.register()


@persistent
def _load_post_handler(dummy):
    wm = bpy.context.window_manager
    wm.cpp_running = False
    wm.cpp_suspended = False
    bpy.ops.cpp.listener('INVOKE_DEFAULT')


@persistent
def _save_pre_handler(dummy):
    bpy.context.scene.cpp.cameras_hide_set(state = False)


@persistent
def _save_post_handler(dummy):
    from .utils import utils_poll
    if utils_poll.full_poll(bpy.context):
        bpy.context.scene.cpp.cameras_hide_set(state = True)


def register_handlers():
    from bpy.app import handlers
    handlers.load_post.append(_load_post_register)
    handlers.load_post.append(_load_post_handler)
    handlers.save_pre.append(_save_pre_handler)
    handlers.save_post.append(_save_post_handler)


def unregister_handlers():
    from bpy.app import handlers
    handlers.save_post.remove(_save_post_handler)
    handlers.save_pre.remove(_save_pre_handler)
    handlers.load_post.remove(_load_post_handler)
    handlers.load_post.remove(_load_post_register)


# Addon register
def register():
    register_handlers()
    bpy.utils.register_class(operators.CPP_OT_info)
    bpy.utils.register_class(preferences.CppPreferences)


def unregister():
    for op in operators.modal_ops:
        cancel = getattr(op, "cancel", None)
        if cancel:
            cancel(bpy.context)
    if _reg:
        keymap.unregister()
        overwrite_ui.unregister()
        extend_bpy_types.unregister_types()

        for cls in reversed(_classes):
            bpy.utils.unregister_class(cls)
        bpy.utils.unregister_class(preferences.CppPreferences)
        bpy.utils.unregister_class(operators.CPP_OT_info)
        icons.unregister()
        unregister_handlers()
