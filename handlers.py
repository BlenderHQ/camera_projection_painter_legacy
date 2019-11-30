import bpy
from bpy.app import handlers

from . import overwrite_ui

__all__ = ["register", "unregister"]


@handlers.persistent
def load_handler(dummy):
    bpy.ops.cpp.camera_projection_painter('INVOKE_DEFAULT')
    overwrite_ui.register()


def register():
    bpy.app.handlers.load_post.append(load_handler)


def unregister():
    bpy.app.handlers.load_post.remove(load_handler)
    overwrite_ui.unregister()
