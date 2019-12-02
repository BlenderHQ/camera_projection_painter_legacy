import os

import bpy
from mathutils import Vector

from .common import flerp, get_hovered_region_3d
from ..constants import AUTOCAM_MIN, AUTOCAM_MAX


def get_camera_attributes(ob):
    camera_size = ob.data.sensor_width
    matrix_world = ob.matrix_world
    camera_pos = ob.matrix_world.translation
    camera_forward = (
            matrix_world.translation + (
            Vector([0.0, 0.0, -ob.data.lens / camera_size]) @ matrix_world.inverted()))

    camera_up = (Vector([0.0, 1.0, 0.0]) @ matrix_world.inverted())

    return camera_pos, camera_forward, camera_up


def bind_camera_image_by_name(ob, file_path):
    ob_name, ob_ext = os.path.splitext(ob.name)

    res_image = None
    for img in bpy.data.images:
        img_name, img_ext = os.path.splitext(img.name)
        if img_name == ob_name:
            size_x, size_y = img.cpp.static_size
            if size_x and size_y:
                res_image = img
            break
    if not res_image:
        if file_path != "":
            path = bpy.path.abspath(file_path)
            if os.path.isdir(path):
                file_list = [n for n in os.listdir(path) if os.path.isfile(os.path.join(path, n))]
                for file_name in file_list:
                    img_name, img_ext = os.path.splitext(file_name)

                    if img_name == ob_name:
                        img_path = os.path.join(path, file_name)
                        if file_name in bpy.data.images:
                            bpy.data.images[file_name].filepath = img_path
                        else:
                            bpy.ops.image.open(filepath = img_path, relative_path = False)
                        if file_name in bpy.data.images:
                            res_image = bpy.data.images[file_name]
                        break
    if res_image:
        size_x, size_y = res_image.cpp.static_size
        if size_x and size_y:
            ob.data.cpp.used = True
            ob.data.cpp.image = res_image
            return res_image.name
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
