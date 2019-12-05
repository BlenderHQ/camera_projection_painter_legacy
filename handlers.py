import bpy
from bpy.app import handlers

from .utils import utils_poll
from . import overwrite_ui

__all__ = ["register", "unregister"]


@handlers.persistent
def load_handler(dummy):
    bpy.ops.cpp.camera_projection_painter('INVOKE_DEFAULT')
    overwrite_ui.register()


@handlers.persistent
def save_pre_handler(dummy):
    bpy.context.scene.cpp.cameras_hide_set(state = False)


@handlers.persistent
def save_post_handler(dummy):
    if utils_poll.full_poll(bpy.context):
        bpy.context.scene.cpp.cameras_hide_set(state = True)


def register():
    bpy.app.handlers.load_post.append(load_handler)
    bpy.app.handlers.save_pre.append(save_pre_handler)
    bpy.app.handlers.save_post.append(save_post_handler)


def unregister():
    bpy.app.handlers.load_post.remove(load_handler)
    overwrite_ui.unregister()
