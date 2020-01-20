# <pep8 compliant>

import importlib

import bpy

from . import camera
from . import image_preview

if "_rc" in locals(): # In case of module reloading 
    importlib.reload(camera)
    importlib.reload(image_preview)

_rc = None

CPP_GGT_camera_gizmo_group = camera.CPP_GGT_camera_gizmo_group
CPP_GT_current_image_preview = image_preview.CPP_GT_current_image_preview
CPP_GGT_image_preview_gizmo_group = image_preview.CPP_GGT_image_preview_gizmo_group

_classes = [
    CPP_GGT_camera_gizmo_group,
    CPP_GT_current_image_preview,
    CPP_GGT_image_preview_gizmo_group
]

register, unregister = bpy.utils.register_classes_factory(_classes)
