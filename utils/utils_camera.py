import os

import bpy
from mathutils import Vector

from .common import flerp, get_hovered_region_3d

AUTOCAM_MIN = 0.852
AUTOCAM_MAX = 0.999


def get_camera_attributes(ob):
    camera_size = ob.data.sensor_width
    matrix_world = ob.matrix_world
    camera_pos = ob.matrix_world.translation
    camera_forward = (
            matrix_world.translation + (
            Vector([0.0, 0.0, -ob.data.lens / camera_size]) @ matrix_world.inverted()))

    camera_up = (Vector([0.0, 1.0, 0.0]) @ matrix_world.inverted())

    return camera_pos, camera_forward, camera_up


def bind_camera_image_by_name(ob, file_list):
    if ob.type == 'CAMERA':
        res = None

        for image in bpy.data.images:
            name, ext = os.path.splitext(image.name)
            if ob.name == image.name or ob.name == name:
                res = image
                break
        if not res:
            for file_path in file_list:
                file_name = bpy.path.basename(file_path)
                name, ext = os.path.splitext(file_name)

                if ob.name == file_name or ob.name == name:

                    if file_name in bpy.data.images:
                        bpy.data.images[file_name].filepath = file_path
                        res = bpy.data.images[file_path]
                    else:
                        res = bpy.data.images.load(filepath = file_path, check_existing = True)
                    break
        if res:
            if not res.cpp.invalid:
                ob.data.cpp.image = res
            return res
        ob.data.cpp.image = None


def set_camera_by_view(context, mouse_position):
    rw3d = get_hovered_region_3d(context, mouse_position)
    if not rw3d:
        return

    scene = context.scene

    method = scene.cpp.auto_set_camera_method
    cam_angles = {}

    for camera in scene.cpp.available_camera_objects:
        camera.select_set(False)
        if method == 'FULL':
            view_rotation = rw3d.view_rotation
            if camera.rotation_mode != 'QUATERNION':
                camera.rotation_mode = 'QUATERNION'
            cam_rot_quat = camera.rotation_quaternion.normalized()
            fac = abs(view_rotation.rotation_difference(cam_rot_quat).w)
            value = flerp(AUTOCAM_MIN, AUTOCAM_MAX, fac)
            if value > scene.cpp.tolerance_full:
                cam_angles[camera] = value

        elif method == 'DIRECTION':
            view_rotation = rw3d.view_rotation @ Vector((0.0, 0.0, -1.0))
            mat = camera.matrix_world
            camera_vec = -Vector((mat[0][2], mat[1][2], mat[2][2]))
            fac = camera_vec.dot(view_rotation)
            value = flerp(AUTOCAM_MIN, AUTOCAM_MAX, fac)
            if value > scene.cpp.tolerance_direction:
                cam_angles[camera] = value

    if not cam_angles:
        return

    view_loc = rw3d.view_matrix.inverted().translation
    index = 0
    if len(cam_angles) > 1:
        distances = [(view_loc - n.location).length for n in cam_angles.keys()]
        index = distances.index(min(distances))

    camera_ob = list(cam_angles.keys())[index]

    camera_ob.select_set(True)
    scene.camera = camera_ob
