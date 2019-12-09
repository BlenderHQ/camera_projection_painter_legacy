import time

import bpy
from bpy.app import handlers

from .utils import utils_poll
from . import overwrite_ui

__all__ = ["register", "unregister"]


@handlers.persistent
def load_handler(dummy):
    overwrite_ui.register()


@handlers.persistent
def save_pre_handler(dummy):
    bpy.context.scene.cpp.cameras_hide_set(state = False)


@handlers.persistent
def save_post_handler(dummy):
    if utils_poll.full_poll(bpy.context):
        bpy.context.scene.cpp.cameras_hide_set(state = True)


@handlers.persistent
def depsgraph_update_post_handler(dummy):
    wm = bpy.context.window_manager
    if not wm.cpp_running:
        if utils_poll.full_poll(bpy.context):
            bpy.ops.cpp.camera_projection_painter('INVOKE_DEFAULT')
            wm.cpp_running = True


def register():
    bpy.app.handlers.load_post.append(load_handler)
    bpy.app.handlers.save_pre.append(save_pre_handler)
    bpy.app.handlers.save_post.append(save_post_handler)
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post_handler)


def unregister():
    bpy.app.handlers.load_post.remove(load_handler)
    bpy.app.handlers.save_pre.remove(save_pre_handler)
    bpy.app.handlers.save_post.remove(save_post_handler)
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_post_handler)
    overwrite_ui.unregister()
