import bpy
from mathutils import Vector

import os


def fclamp(value: float, min_value: float, max_value: float):
    return max(min(value, max_value), min_value)


def flerp(value0: float, value1: float, factor: float):
    return (value0 * (1.0 - factor)) + (value1 * factor)


def smooth(a: Vector, b: Vector, fac: float):
    return Vector([(a.x * (1.0 - fac)) + (b.x * fac), (a.y * (1.0 - fac)) + (b.y * fac)])


def iter_curve_values(curve_mapping, steps: int):
    curve_mapping.initialize()
    curve = list(curve_mapping.curves)[0]
    clip_min_x = curve_mapping.clip_min_x
    clip_min_y = curve_mapping.clip_min_y
    clip_max_x = curve_mapping.clip_max_x
    clip_max_y = curve_mapping.clip_max_y

    for i in range(steps):
        fac = i / steps
        pos = flerp(clip_min_x, clip_max_x, fac)
        value = curve.evaluate(pos)
        yield fclamp(value, clip_min_y, clip_max_y)


def check_images_startup(self, context):
    scene = context.scene
    cameras = scene.cpp.available_camera_objects
    missing_count = 0
    for ob in cameras:
        camera = ob.data
        image = camera.cpp.image
        if image.filepath == "":
            continue
        fp = bpy.path.abspath(image.filepath)

        if not os.path.isfile(fp):
            camera.cpp.used = False
            camera.cpp.image = None
            missing_count += 1
            print("Camera: %s\nMissing file path: %s\n" % (ob.name, fp))
    if missing_count:
        self.report(type = {'WARNING'}, message = "Missing data for %d cameras!" % missing_count)


def get_active_rv3d(context, mouse_position):
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            mouse_x, mouse_y = mouse_position

            if (area.x <= mouse_x < (area.x + area.width) and
                    area.y <= mouse_y < (area.y + area.height)):
                if len(area.spaces.active.region_quadviews) > 0:
                    header = next(r for r in area.regions if r.type == 'HEADER')

                    quad_w = area.width / 2
                    quad_h = (area.height - header.height) / 2
                    quad_0_x = area.x
                    quad_0_y = area.y + header.height
                    quad_1_x = area.x
                    quad_1_y = area.y + quad_h + header.height
                    quad_2_x = area.x + quad_w
                    quad_2_y = area.y + header.height

                    if (quad_0_x <= mouse_x < (quad_0_x + quad_w) and
                            quad_0_y <= mouse_y < (quad_0_y + quad_h)):
                        return area.spaces.active.region_quadviews[0]

                    if (quad_1_x <= mouse_x < (quad_1_x + quad_w) and
                            quad_1_y <= mouse_y < (quad_1_y + quad_h)):
                        return area.spaces.active.region_quadviews[1]

                    if (quad_2_x <= mouse_x < (quad_2_x + quad_w) and
                            quad_2_y <= mouse_y < (quad_2_y + quad_h)):
                        return area.spaces.active.region_quadviews[2]

                    return area.spaces.active.region_quadviews[3]
                else:
                    return area.spaces.active.region_3d
