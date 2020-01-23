# <pep8 compliant>

import bpy
from bpy_extras import view3d_utils
from mathutils import Vector, Matrix


_image_loading_order = []


def gl_load(context, image: bpy.types.Image):
    scene = context.scene
    for index, item in enumerate(_image_loading_order):
        try:
            if (not item) or (not item.cpp.valid) or (not item.has_data):
                _image_loading_order.pop(index)
        except ReferenceError:
            _image_loading_order.pop(index)

    if not image.gl_load():
        if image in _image_loading_order:
            _image_loading_order.remove(image)
        _image_loading_order.insert(0, image)
        if len(_image_loading_order) > scene.cpp.max_loaded_images:
            last_image = _image_loading_order[-1]
            last_image.gl_free()
            last_image.buffers_free()
            _image_loading_order.remove(last_image)

    elif image in _image_loading_order:
        _image_loading_order.remove(image)


def clear_image_loading_order():
    global _image_loading_order
    _image_loading_order = []


def ray_cast(context, mpos):
    ob = context.active_object
    scene = context.scene
    region = context.region
    rv3d = context.region_data

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, mpos)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, mpos)

    ray_target = ray_origin + view_vector

    # get the ray relative to the object
    matrix_inv = ob.matrix_world.inverted()
    ray_origin_obj = matrix_inv @ ray_origin
    ray_target_obj = matrix_inv @ ray_target
    ray_direction_obj = ray_target_obj - ray_origin_obj

    # cast the ray
    success, location, normal, face_index = ob.ray_cast(
        ray_origin_obj, ray_direction_obj)

    if success:
        location = ob.matrix_world @ location
        distance = (ray_origin - location).length
        return distance
    return -1


def _get_check_pattern():
    from math import radians
    pattern = []
    p0 = Vector((1.0, 0.0, 0.0))
    for i in range(8):
        angle = radians(45 * i)
        mat_rotation = Matrix.Rotation(angle, 3, 'Z')
        p1 = p0.copy()
        p1.rotate(mat_rotation)
        pattern.append(p1.to_2d())
    pattern.append(Vector((0.0, 0.0)))
    return pattern

CHECK_PATTERN = _get_check_pattern()  # do it at stage of import, it's constant


def get_warning_status(context, mpos):
    mpos = Vector(mpos)

    scene = context.scene
    region = context.region
    rv3d = context.region_data

    brush_radius = scene.tool_settings.unified_paint_settings.size

    p0 = view3d_utils.region_2d_to_vector_3d(region, rv3d, mpos)
    p1 = view3d_utils.region_2d_to_vector_3d(
        region, rv3d, (mpos[0] + brush_radius, mpos[1]))
    scr_radius = (p0 - p1).length

    lens = context.space_data.lens * 0.01  # convert to meters

    distances = []
    for p in CHECK_PATTERN:
        ppos = mpos + (p * brush_radius)
        dist = ray_cast(context, ppos)
        if dist != -1:
            distances.append(dist)

    distance = 0.0
    if distances:
        distance = sum(distances) / len(distances)

    if distance != -1:
        a = scr_radius
        b = lens
        tan_a = a / b
        unprojected_radius = tan_a * distance
        if unprojected_radius > scene.cpp.distance_warning:
            return True

    return False


def danger_zone_popup_menu(self, context):
    layout = self.layout

    layout.emboss = 'NONE'

    scene = context.scene

    layout.label(text="Safe Options:")
    layout.separator()
    row = layout.row()

    col = row.column()
    col.label(text="Unprojected Radius:")

    col = row.column()
    col.emboss = 'NORMAL'
    col.label(text="%d %s" % (
        scene.cpp.distance_warning,
        str(scene.unit_settings.length_unit).capitalize()))
