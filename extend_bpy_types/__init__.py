from . import camera
from . import scene
from . import image
from . import node
from . import wm

if "bpy" in locals():
    import importlib
    importlib.reload(camera)
    importlib.reload(scene)
    importlib.reload(image)
    importlib.reload(node)
    importlib.reload(wm)

import bpy
from bpy.props import BoolProperty, PointerProperty, CollectionProperty
from bpy.types import Camera, Object, Scene, ShaderNodeTree, Image, WindowManager


_classes = [
    wm.ProgressItem,
    wm.WindowManagerProperties,
    camera.BindImageHistoryItem,
    camera.CameraProperties,
    scene.SceneProperties,
    image.ImageProperties,
]

_cls_register, _cls_unregister = bpy.utils.register_classes_factory(_classes)


def register():
    _cls_register()

    Camera.cpp = PointerProperty(type=camera.CameraProperties)
    Scene.cpp = PointerProperty(type=scene.SceneProperties)
    Image.cpp = PointerProperty(type=image.ImageProperties)
    WindowManager.cpp = PointerProperty(type=wm.WindowManagerProperties)
    WindowManager.cpp_progress_seq = CollectionProperty(type=wm.ProgressItem)

    ShaderNodeTree.active_texnode_index = node.active_texnode_index
    Object.initial_visible = BoolProperty(name="Used", default=True)
    Camera.cpp_bind_history = CollectionProperty(type=camera.BindImageHistoryItem)


def unregister():
    _cls_unregister()

    del Camera.cpp_bind_history
    del Camera.cpp
    del Scene.cpp
    del Image.cpp
    del WindowManager.cpp
    del ShaderNodeTree.active_texnode_index
    del Object.initial_visible
