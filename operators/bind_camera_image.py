# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(utils)

    del importlib
else:
    from .. import utils

import bpy
import os


class CPP_OT_bind_camera_image(bpy.types.Operator):
    bl_idname = "cpp.bind_camera_image"
    bl_label = "Bind Image By Name"
    bl_description = "Find image with equal name to camera name.\n" \
                     "If no image packed into .blend, search in Source Images path. (See Scene tab)"
    bl_options = {'REGISTER'}

    mode: bpy.props.EnumProperty(
        items = [('ACTIVE', "Active", ""),
                 ('CONTEXT', "Context", ""),
                 ('SELECTED', "Selected", ""),
                 ('ALL', "All", ""),
                 ('TMP', "Tmp", "")],
        name = "Mode",
        default = 'ACTIVE')

    def execute(self, context):
        scene = context.scene
        source_images_path = bpy.path.native_pathsep(bpy.path.abspath(scene.cpp.source_images_path))

        cameras = []
        if self.mode == 'ACTIVE':
            ob = context.active_object
            cameras = [ob] if ob.type == 'CAMERA' else []
        elif self.mode == 'CONTEXT':
            cameras = [scene.camera]
        elif self.mode == 'SELECTED':
            cameras = scene.cpp.selected_camera_objects
        elif self.mode == 'ALL':
            cameras = scene.cpp.camera_objects
        elif self.mode == 'TMP':
            wm = context.window_manager
            ob = wm.cpp_current_selected_camera_ob
            if ob:
                cameras = [ob] if ob.type == 'CAMERA' else []
        count = 0

        file_list = []
        if os.path.isdir(source_images_path):
            file_list = [
                bpy.path.native_pathsep(os.path.join(source_images_path, n)) for n in os.listdir(source_images_path)
            ]

        for ob in cameras:
            res = utils.common.bind_camera_image_by_name(ob, file_list)
            if res:
                count += 1
                # Also print list of successfully binded cameras to console
                print("Camera: %s - Image: %s" % (ob.name, res.name))

        if count:
            mess = "Binded %d camera images" % count
            if count == 1:
                mess = "Binded %s camera image" % res.name
            self.report(type = {'INFO'}, message = mess)
        else:
            self.report(type = {'WARNING'}, message = "Images not found!")

        return {'FINISHED'}
