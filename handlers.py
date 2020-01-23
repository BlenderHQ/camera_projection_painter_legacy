# <pep8 compliant>

import bpy
from bpy.app.handlers import persistent


@persistent
def load_post_handler(dummy=None):
    # start listener
    wm = bpy.context.window_manager
    wm.cpp_running = False
    wm.cpp_suspended = False
    bpy.ops.cpp.listener('INVOKE_DEFAULT')


@persistent
def save_pre_handler(dummy=None):
    wm = bpy.context.window_manager
    if wm.cpp_running:
        # Save file with visible cameras
        bpy.context.scene.cpp.cameras_hide_set(state=False)


@persistent
def save_post_handler(dummy=None):
    from . import poll
    if poll.full_poll(bpy.context):
        # Hide cameras back after saving the file
        bpy.context.scene.cpp.cameras_hide_set(state=True)


@persistent
def depsgraph_update_pre_handler(scene=None):
    from . import poll
    if poll.full_poll(bpy.context):
        # Remove missing images from the list of the camera palette
        for camera_object in scene.cpp.camera_objects:
            camera = camera_object.data

            for item_index, item in enumerate(camera.cpp_bind_history):
                if not item.image:
                    camera.cpp_bind_history.remove(item_index)


_handlers = (
    (bpy.app.handlers.load_post, load_post_handler),
    (bpy.app.handlers.save_pre, save_pre_handler),
    (bpy.app.handlers.save_post, save_post_handler),
    (bpy.app.handlers.depsgraph_update_pre, depsgraph_update_pre_handler)
)


def register():
    for handle, func in _handlers:
        handle.append(func)


def unregister():
    for handle, func in _handlers:
        if func in handle:
            handle.remove(func)
