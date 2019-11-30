import bpy
import bmesh
from mathutils import Vector

from ..constants import TEMP_DATA_NAME

import time


class PropertyTracker(object):
    __slots__ = ("value",)

    def __init__(self, value = None):
        self.value = value

    def __call__(self, value = None):
        if self.value != value:
            self.value = value
            return True
        return False


# Operator cls specific func

def set_properties_defaults(self):
    """
    Set default values at startup and after exit available context
    """
    self.suspended = False
    self.suspended_mouse = False
    self.setup_required = True

    self.draw_handler = None

    self.bm = None
    self.mesh_batch = None
    self.camera_batches = {}

    self.brush_texture_bindcode = 0
    self.data_updated = PropertyTracker()
    self.check_brush_curve_updated = PropertyTracker()

    self.mouse_position = (0, 0)


# Base utils

def get_bmesh(context, ob):
    """
    Get bmesh from evaluated depsgraph
    :param context: bpy.types.Context
    :param ob: bpy.types.Object
    :return: bmesh.types.Bmesh
    """
    bm = bmesh.new()
    depsgraph = context.evaluated_depsgraph_get()
    bm.from_object(object = ob, depsgraph = depsgraph, deform = True, cage = False, face_normals = False)
    return bm


def remove_uv_layer(ob):
    """
    Remove temporary uv layer from given object
    :param bpy.types.Object:
    :return: None
    """
    if ob:
        if ob.type == 'MESH':
            uv_layers = ob.data.uv_layers
            if TEMP_DATA_NAME in uv_layers:
                uv_layers.remove(uv_layers[TEMP_DATA_NAME])


def set_clone_image_from_camera_data(context):
    scene = context.scene
    camera = scene.camera.data
    image_paint = scene.tool_settings.image_paint
    if camera.cpp.available:
        image = camera.cpp.image
        if image:
            if image_paint.clone_image != image:
                image_paint.clone_image = image


def setup_basis_uv_layer(context):
    scene = context.scene
    image_paint = scene.tool_settings.image_paint
    clone_image = image_paint.clone_image
    ob = context.image_paint_object
    uv_layers = ob.data.uv_layers

    if TEMP_DATA_NAME not in uv_layers:
        uv_layers.new(name = TEMP_DATA_NAME, do_init = False)
        uv_layer = uv_layers[TEMP_DATA_NAME]
        uv_layer.active = False
        uv_layer.active_clone = True

    if TEMP_DATA_NAME not in ob.modifiers:
        bpy.ops.object.modifier_add(type = 'UV_PROJECT')
        modifier = ob.modifiers[-1]
        modifier.name = TEMP_DATA_NAME

    modifier = ob.modifiers[TEMP_DATA_NAME]
    uv_layer = uv_layers[TEMP_DATA_NAME]

    while ob.modifiers[0] != modifier:  # Required when object already has some modifiers on it
        bpy.ops.object.modifier_move_up(modifier = modifier.name)

    modifier.uv_layer = uv_layer.name

    modifier.scale_x = 1.0
    modifier.scale_y = 1.0

    size_x, size_y = clone_image.cpp.static_size

    if size_x > size_y:
        modifier.aspect_x = size_x / size_y
        modifier.aspect_y = 1.0
    elif size_y > size_x:
        modifier.aspect_x = 1.0
        modifier.aspect_y = size_x / size_y
    else:
        modifier.aspect_x = 1.0
        modifier.aspect_y = 1.0

    modifier.projector_count = 1
    modifier.projectors[0].object = scene.camera

    bpy.ops.object.modifier_apply(modifier = TEMP_DATA_NAME)


def deform_uv_layer(self, context):
    ob = context.image_paint_object

    bm = self.bm

    uv_layer = bm.loops.layers.uv.get(TEMP_DATA_NAME)

    dt = time.time()

    for face in bm.faces:
        for loop in face.loops:
            loop_uv = loop[uv_layer]
            # use xy position of the vertex as a uv coordinate
            loop_uv.uv = Vector(loop_uv.uv)  # + Vector((0.005, 0.005))

    bm.to_mesh(ob.data)

    print("deform", time.time() - dt)
