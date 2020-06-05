import bpy
from bpy.app.handlers import persistent


@persistent
def load_post_handler(dummy=None):
    wm = bpy.context.window_manager

    wm.cpp.running = False
    wm.cpp.suspended = False
    bpy.ops.cpp.listener('INVOKE_DEFAULT')


@persistent
def save_pre_handler(dummy=None):
    wm = bpy.context.window_manager
    if wm.cpp.running:
        for ob in bpy.context.scene.cpp.camera_objects:
            ob.hide_set(not ob.initial_visible)


@persistent
def save_post_handler(dummy=None):
    from . import poll
    if poll.full_poll(bpy.context):
        for ob in bpy.context.scene.cpp.camera_objects:
            ob.hide_set(True)


@persistent
def depsgraph_update_pre_handler(scene=None):
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
