# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(utils)

    del importlib
else:
    from .. import utils

import bpy


class CPP_OT_enter_context(bpy.types.Operator):
    bl_idname = "cpp.enter_context"
    bl_label = "Setup Context"

    @classmethod
    def poll(cls, context):
        if utils.poll.full_poll(context):
            return False
        ob = context.active_object
        if not ob:
            return False
        if ob.type != 'MESH':
            return False
        scene = context.scene
        if not scene.cpp.has_camera_objects:
            return True
        return True

    @classmethod
    def description(cls, context, properties):
        ob = context.active_object
        scene = context.scene
        image_paint = scene.tool_settings.image_paint

        res = ""
        _num = 1

        if ob.mode != 'TEXTURE_PAINT':
            res += "%s. Object mode will be changed to Texture Paint" % _num
            res += "\n"
            _num += 1

        tool = context.workspace.tools.from_space_view3d_mode(context.mode, create = False)
        if tool.idname != "builtin_brush.Clone":
            res += "%s. Tool will be set to Clone" % _num
            res += "\n"
            _num += 1

        if image_paint.mode != 'IMAGE':
            res += "%s. Image Paint Mode will be set to Single Image" % _num
            res += "\n"
            _num += 1

        if not image_paint.use_clone_layer:
            res += "%s. Image Paint will Use Clone Layer" % _num
            res += "\n"
            _num += 1

        if scene.cpp.mapping != 'CAMERA':
            res += "%s. Image Paint Mapping will be set to Camera" % _num
            res += "\n"
            _num += 1

        if not scene.cpp.use_auto_set_image:
            res += "%s. Image Paint Auto Set Image will be set to True" % _num
            res += "\n"
            _num += 1

        camera_ob = scene.camera
        if not camera_ob:
            if scene.cpp.has_available_camera_objects:
                camera_ob = list(scene.cpp.available_camera_objects)[0]
                res += "%s. Scene camera will be set to %s" % (_num, camera_ob.name)
                res += "\n"
                _num += 1

        if camera_ob:
            image = camera_ob.data.cpp.image
            if image:
                if not image.cpp.invalid:
                    if image != image_paint.clone_image:
                        res += "%s. Image Paint Clone Image will be set to %s" % (_num, image.name)
                        res += "\n"
                        _num += 1

        if not res:
            res = "Context is ready"

        return res

    def execute(self, context):
        ob = context.active_object
        scene = context.scene
        image_paint = scene.tool_settings.image_paint

        if ob.mode != 'TEXTURE_PAINT':
            bpy.ops.object.mode_set(mode = 'TEXTURE_PAINT')

        tool = context.workspace.tools.from_space_view3d_mode(context.mode, create = False)
        if tool.idname != "builtin_brush.Clone":
            bpy.ops.wm.tool_set_by_id(name = "builtin_brush.Clone", cycle = False, space_type = 'VIEW_3D')

        if image_paint.mode != 'IMAGE':
            image_paint.mode = 'IMAGE'

        if not image_paint.use_clone_layer:
            image_paint.use_clone_layer = True

        if scene.cpp.mapping != 'CAMERA':
            scene.cpp.mapping = 'CAMERA'

        if not scene.cpp.use_auto_set_image:
            scene.cpp.use_auto_set_image = True

        if not scene.camera:
            if scene.cpp.has_available_camera_objects:
                scene.camera = list(scene.cpp.available_camera_objects)[0]

        if scene.camera:
            image = scene.camera.data.cpp.image
            if image:
                if not image.cpp.invalid:
                    image_paint.clone_image = image

        return {'FINISHED'}
