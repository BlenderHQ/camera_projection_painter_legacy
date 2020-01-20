# <pep8 compliant>

import importlib
import numpy as np

import bpy
import bgl
import gpu
from mathutils import Vector
from bpy.types import SpaceView3D
from gpu_extras.batch import batch_for_shader

from . import cameras
from . import mesh_preview

if "_rc" in locals():
    importlib.reload(cameras)
    importlib.reload(mesh_preview)

_rc = None


_image_previews = {}
_image_icons = {}
_image_skip_free = set({})

# Class methods for controlling rendering in a viewport

def add_draw_handlers(self, context):
    args = (self, context)
    callback = mesh_preview.draw_projection_preview
    self.draw_handler = SpaceView3D.draw_handler_add(callback, args, 'WINDOW', 'POST_VIEW')
    callback = cameras.draw_cameras
    self.draw_handler_cameras = SpaceView3D.draw_handler_add(callback, args, 'WINDOW', 'POST_VIEW')


def remove_draw_handlers(self):
    if self.draw_handler:
        SpaceView3D.draw_handler_remove(self.draw_handler, 'WINDOW')
    if self.draw_handler_cameras:
        SpaceView3D.draw_handler_remove(self.draw_handler_cameras, 'WINDOW')
