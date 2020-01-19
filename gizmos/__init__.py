# <pep8 compliant>

if "bpy" in locals(): # In case of module reloading 
    import importlib

    importlib.reload(camera)
    importlib.reload(image_preview)

    del importlib
else:
    from . import camera
    from . import image_preview

import bpy

CPP_GGT_camera_gizmo_group = camera.CPP_GGT_camera_gizmo_group
CPP_GT_current_image_preview = image_preview.CPP_GT_current_image_preview
CPP_GGT_image_preview_gizmo_group = image_preview.CPP_GGT_image_preview_gizmo_group

_classes = [
    CPP_GGT_camera_gizmo_group,
    CPP_GT_current_image_preview,
    CPP_GGT_image_preview_gizmo_group
]

register, unregister = bpy.utils.register_classes_factory(_classes)
