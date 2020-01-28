# <pep8 compliant>

import importlib

import bpy

from . import utils


if "_rc" in locals():
    importlib.reload(utils)

_rc = None


def operator_execute(self, context):
    """Operator Execution Method"""
    active_object = context.active_object
    scene = context.scene
    image_paint = scene.tool_settings.image_paint

    object_material = active_object.active_material

    if self.reverse:
        if not object_material.use_nodes:
            self.report(type={'WARNING'}, message="Active material does not use nodes!")
            return {'CANCELLED'}

        result = utils.material.set_material_diffuse_to_canvas(image_paint, object_material)
        if result == -1:
            self.report(type={'INFO'}, message="Canvas set of diffuse texture")
        elif result == 1:
            self.report(type={'WARNING'}, message="The material has no active output!")
        elif result == 2:
            self.report(type={'WARNING'}, message="Invalid image found in nodes!")
        elif result == 3:
            self.report(type={'WARNING'}, message="Image not found!")

    else:
        result = utils.material.set_canvas_to_material_diffuse(object_material, image_paint.canvas)
        if result == -1:
            self.report(type={'INFO'}, message="Diffuse texture set from canvas")
        else:
            self.report(type={'WARNING'}, message="Failed to set diffuse texture from canvas!")

    return {'FINISHED'}


class CPP_OT_canvas_to_diffuse(bpy.types.Operator):
    bl_idname = "cpp.canvas_to_diffuse"
    bl_label = "Set Canvas To Diffuse"

    bl_options = {'REGISTER', 'UNDO'}

    reverse: bpy.props.BoolProperty(default=False)

    @classmethod
    def description(cls, context, properties):
        if properties.reverse:
            return "Search for a diffuse texture node and set it as a canvas"
        else:
            return "Setting an image in a diffuse texture node with creating missing nodes"

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        if not ob:
            return False
        return ob.active_material

    execute = operator_execute
