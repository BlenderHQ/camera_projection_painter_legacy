import bpy
from bpy.app.handlers import persistent

from .utils import utils_poll


@persistent
def load_post_handler(dummy):
    bpy.ops.cpp.listener('INVOKE_DEFAULT')

@persistent
def depsgraph_update_post_handler(scene):
    wm = bpy.context.window_manager
    if not wm.cpp_running:
        if utils_poll.full_poll(bpy.context):
            wm.cpp_running = True
            wm.cpp_suspended = False
            bpy.ops.cpp.camera_projection_painter('INVOKE_DEFAULT')


@persistent
def save_pre_handler(dummy):
    bpy.context.scene.cpp.cameras_hide_set(state = False)


@persistent
def save_post_handler(dummy):
    if utils_poll.full_poll(bpy.context):
        bpy.context.scene.cpp.cameras_hide_set(state = True)


def register():
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post_handler)
    bpy.app.handlers.load_post.append(load_post_handler)
    bpy.app.handlers.save_pre.append(save_pre_handler)
    bpy.app.handlers.save_post.append(save_post_handler)


def unregister():
    bpy.app.handlers.save_post.remove(save_post_handler)
    bpy.app.handlers.save_pre.remove(save_pre_handler)
    bpy.app.handlers.load_post.remove(load_post_handler)
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_post_handler)
