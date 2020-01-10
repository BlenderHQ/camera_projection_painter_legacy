# <pep8 compliant>

if "bpy" in locals():
    import importlib

    importlib.reload(utils)

    del importlib
else:
    from .. import utils

import bpy


class CPP_OT_canvas_to_diffuse(bpy.types.Operator):
    bl_idname = "cpp.canvas_to_diffuse"
    bl_label = "Set Canvas To Diffuse"

    bl_options = {'REGISTER', 'UNDO'}

    reverse: bpy.props.BoolProperty(default = False)

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

    def execute(self, context):
        ob = context.active_object
        scene = context.scene
        image_paint = scene.tool_settings.image_paint

        material = ob.active_material

        if self.reverse:
            print("set_material_diffuse_to_canvas")
            if not material.use_nodes:
                self.report(type = {'WARNING'}, message = "Material not using nodes!")
                return {'CANCELLED'}

            res = utils.common.set_material_diffuse_to_canvas(image_paint, material)
            if res == -1:
                self.report(type = {'INFO'}, message = "Successfully set Canvas from Diffuse")
            elif res == 1:
                self.report(type = {'WARNING'}, message = "Material have no active output!")
            elif res == 2:
                self.report(type = {'WARNING'}, message = "Found invalid image from nodes!")
            elif res == 3:
                self.report(type = {'WARNING'}, message = "Image not found!")

        else:
            print("set_canvas_to_material_diffuse")
            res = utils.common.set_canvas_to_material_diffuse(material, image_paint.canvas)

        return {'FINISHED'}
