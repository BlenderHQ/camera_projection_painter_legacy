# <pep8 compliant>

import importlib

import bpy
from mathutils import Vector

from . import screen
from . import common

if "_rc" in locals():
    importlib.reload(screen)
    importlib.reload(common)

_rc = None


AUTOCAM_MIN = 0.852
AUTOCAM_MAX = 0.999


def set_clone_image_from_camera_data(context):
    scene = context.scene
    if scene.camera:
        camera = scene.camera.data
        image_paint = scene.tool_settings.image_paint
        if camera.cpp.available:
            image = camera.cpp.image
            if image:
                if image_paint.clone_image != image:
                    image_paint.clone_image = image


def set_camera_by_view(context, rv3d, mouse_position):
    if not rv3d:
        return

    scene = context.scene

    set_camera_method = scene.cpp.auto_set_camera_method
    cam_angles = {}

    for camera_object in scene.cpp.available_camera_objects:
        if camera_object.cpp.initial_hide_viewport:
            continue

        if set_camera_method == 'FULL':
            view_rotation = rv3d.view_rotation
            if camera_object.rotation_mode != 'QUATERNION':
                camera_object.rotation_mode = 'QUATERNION'
            cam_rot_quat = camera_object.rotation_quaternion.normalized()
            fac = abs(view_rotation.rotation_difference(cam_rot_quat).w)
            value = common.f_lerp(AUTOCAM_MIN, AUTOCAM_MAX, fac)
            if value > scene.cpp.tolerance_full:
                cam_angles[camera_object] = value

        elif set_camera_method == 'DIRECTION':
            view_rotation = rv3d.view_rotation @ Vector((0.0, 0.0, -1.0))
            mat = camera_object.matrix_world
            camera_vec = -Vector((mat[0][2], mat[1][2], mat[2][2]))
            fac = camera_vec.dot(view_rotation)
            value = common.f_lerp(AUTOCAM_MIN, AUTOCAM_MAX, fac)
            if value > scene.cpp.tolerance_direction:
                cam_angles[camera_object] = value

    if not cam_angles:
        return

    view_loc = rv3d.view_matrix.inverted().translation
    index = 0
    if len(cam_angles) > 1:
        distances = [(view_loc - n.location).length for n in cam_angles.keys()]
        index = distances.index(min(distances))

    new_camera_object = list(cam_angles.keys())[index]

    scene.camera = new_camera_object
