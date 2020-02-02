# <pep8 compliant>

import importlib

import bpy

from . import camera
from . import context_menu
from . import image_paint
from . import scene
from . import preset_menus
from . import template


if "_rc" in locals():  # In case of module reloading
    importlib.reload(camera)
    importlib.reload(context_menu)
    importlib.reload(image_paint)
    importlib.reload(scene)
    importlib.reload(preset_menus)
    importlib.reload(template)

_rc = None


_classes = [
    preset_menus.CPP_MT_workflow_presets,
    
    camera.DATA_UL_bind_history_item,
    camera.CPP_PT_active_camera_options,

    scene.CPP_PT_camera_painter_scene,
    scene.CPP_PT_enter_context,

    image_paint.CPP_PT_camera_painter,

    image_paint.CPP_PT_view_options,
    image_paint.CPP_PT_camera_options,
    image_paint.CPP_PT_view_projection_options,
    image_paint.CPP_PT_current_image_preview_options,

    image_paint.CPP_PT_operator_options,
    image_paint.CPP_PT_material_options,
    image_paint.CPP_PT_camera_selection_options,
    image_paint.CPP_PT_warnings_options,
    image_paint.CPP_PT_current_camera,

    context_menu.CPP_MT_camera_pie
]

register, unregister = bpy.utils.register_classes_factory(_classes)
