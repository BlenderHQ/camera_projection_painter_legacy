# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(constants)
    importlib.reload(utils)

    del importlib
else:
    from ... import constants
    from ... import utils

import bpy
import bmesh


def set_properties_defaults(self):
    """
    Set default values at startup and after exit available context
    """
    self.suspended = False
    self.suspended_mouse = False
    self.suspended_brush = False
    self.setup_required = True
    self.full_draw = False

    self.draw_handler = None

    self.bm = None
    self.mesh_batch = None
    self.axes_batch = None
    self.camera_batch = None
    self.image_rect_batch = None

    self.brush_texture_bindcode = 0
    self.data_updated = utils.common.PropertyTracker()
    self.check_brush_curve_updated = utils.common.PropertyTracker()
    self.check_camera_frame_updated = utils.common.PropertyTracker()


def get_bmesh(context, ob):
    bm = bmesh.new()
    depsgraph = context.evaluated_depsgraph_get()
    bm.from_object(object = ob, depsgraph = depsgraph, deform = True, cage = False, face_normals = False)
    return bm


def remove_uv_layer(ob):
    if ob:
        if ob.type == 'MESH':
            uv_layers = ob.data.uv_layers
            if constants.TEMP_DATA_NAME in uv_layers:
                uv_layers.remove(uv_layers[constants.TEMP_DATA_NAME])


def _ensure_modifier(ob):
    if constants.TEMP_DATA_NAME not in ob.modifiers:
        bpy.ops.object.modifier_add(type = 'UV_PROJECT')
        modifier = ob.modifiers[-1]
        modifier.name = constants.TEMP_DATA_NAME
    assert constants.TEMP_DATA_NAME in ob.modifiers
    modifier = ob.modifiers[constants.TEMP_DATA_NAME]

    modifier.projector_count = 1
    modifier.aspect_x = 1.0
    modifier.aspect_y = 1.0

    while ob.modifiers[0] != modifier:  # Required when object already has some modifiers on it
        bpy.ops.object.modifier_move_up(modifier = modifier.name)

    return modifier


def _ensure_uv_layer(ob):
    uv_layers = ob.data.uv_layers
    if constants.TEMP_DATA_NAME not in uv_layers:
        uv_layers.new(name = constants.TEMP_DATA_NAME, do_init = False)
        uv_layer = uv_layers[constants.TEMP_DATA_NAME]
        uv_layer.active = False
        uv_layer.active_clone = True
    assert constants.TEMP_DATA_NAME in uv_layers
    uv_layer = uv_layers[constants.TEMP_DATA_NAME]

    return uv_layer


def setup_basis_uv_layer(context):
    scene = context.scene
    image_paint = scene.tool_settings.image_paint
    clone_image = image_paint.clone_image

    if clone_image.cpp.invalid:
        return

    ob = context.image_paint_object

    modifier = _ensure_modifier(ob)
    uv_layer = _ensure_uv_layer(ob)

    modifier.uv_layer = uv_layer.name

    modifier.scale_x = 1.0
    modifier.scale_y = clone_image.cpp.aspect

    modifier.projectors[0].object = scene.camera

    bpy.ops.object.modifier_apply(modifier = constants.TEMP_DATA_NAME)

    width, height = clone_image.cpp.static_size
    scene.render.resolution_x = width
    scene.render.resolution_y = height


def deform_uv_layer(self, context):
    bm = self.bm
    ob = context.image_paint_object
    uv_layer = bm.loops.layers.uv.get(constants.TEMP_DATA_NAME)

    # TODO: Camera calibration


def ensure_camera_data_settings(self, camera_object: bpy.types.Object):
    camera = camera_object.data

    camera.type = 'PERSP'
    camera.lens_unit = 'MILLIMETERS'

    camera.shift_x = 0.0
    camera.shift_y = 0.0

    camera.sensor_fit = 'AUTO'