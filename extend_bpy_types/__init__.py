# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(camera)
    importlib.reload(scene)
    importlib.reload(image)
    importlib.reload(window_manager)

    del importlib
else:
    from . import camera
    from . import scene
    from . import image
    from . import window_manager

import bpy
from bpy.props import (
    PointerProperty,
    CollectionProperty
)

BindImageHistory = camera.BindImageHistory
CameraProperties = camera.CameraProperties
SceneProperties = scene.SceneProperties
ImageProperties = image.ImageProperties

_classes = (
    BindImageHistory,
    CameraProperties,
    SceneProperties,
    ImageProperties,
)

_cls_register, _cls_unregister = bpy.utils.register_classes_factory(_classes)


def register():
    _cls_register()

    bpy.types.WindowManager.cpp_running = window_manager.cpp_running
    bpy.types.WindowManager.cpp_suspended = window_manager.cpp_suspended
    bpy.types.WindowManager.cpp_mouse_pos = window_manager.cpp_mouse_pos
    bpy.types.WindowManager.cpp_current_selected_camera_ob = window_manager.cpp_current_selected_camera_ob

    bpy.types.Camera.cpp_bind_history = CollectionProperty(type = BindImageHistory)
    bpy.types.Camera.cpp = PointerProperty(type = CameraProperties)
    bpy.types.Scene.cpp = PointerProperty(type = SceneProperties)
    bpy.types.Image.cpp = PointerProperty(type = ImageProperties)


def unregister():
    _cls_unregister()

    del bpy.types.Image.cpp
    del bpy.types.Scene.cpp
    del bpy.types.Camera.cpp
    del bpy.types.Camera.cpp_bind_history

    del bpy.types.WindowManager.cpp_running
    del bpy.types.WindowManager.cpp_suspended
    del bpy.types.WindowManager.cpp_mouse_pos
    del bpy.types.WindowManager.cpp_current_selected_camera_ob
