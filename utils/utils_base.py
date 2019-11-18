import bpy
import gpu

import bmesh

from ..constants import TEMP_DATA_NAME, TIME_STEP


class PropertyTracker(object):
    __slots__ = ("value",)

    def __init__(self, value = None):
        self.value = value

    def __call__(self, value = None):
        if self.value != value:
            self.value = value
            return True
        return False


class CameraProjectionPainterBaseUtils:
    clone_image: bpy.types.Image
    camera: bpy.types.Object
    image_batch: gpu.types.GPUBatch
    ob_bmesh: bmesh.types.BMesh
    mesh_batch: gpu.types.GPUBatch
    suspended: bool
    draw_handler: object
    setup_required: bool
    brush_texture_bindcode: int

    data_updated: PropertyTracker
    check_brush_curve_updated: PropertyTracker

    def set_properties_defaults(self):
        self.suspended = False
        self.ob_bmesh = None
        self.mesh_batch = None
        self.image_batch = None
        self.draw_handler = None
        self.setup_required = True
        self.brush_texture_bindcode = 0

        self.camera = None
        self.clone_image = None

        self.data_updated = PropertyTracker()
        self.check_brush_curve_updated = PropertyTracker()

    def register_modal(self, context):
        wm = context.window_manager
        wm.event_timer_add(time_step = TIME_STEP, window = context.window)
        wm.modal_handler_add(self)


def generate_bmesh(context):
    ob = context.image_paint_object
    bm = bmesh.new()
    depsgraph = context.evaluated_depsgraph_get()
    bm.from_object(object = ob, depsgraph = depsgraph, deform = True, cage = False, face_normals = False)
    return bm


def remove_uv_layer(context):
    ob = context.active_object
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

    # Scene resolution for background images
    # TODO: Remove next lines
    scene.render.resolution_x = size_x
    scene.render.resolution_y = size_y


def deform_uv_layer(context):
    print("deform")
