import bpy

__all__ = ("active_texnode_index",)


def _get_texnode_index(self):
    image_paint = bpy.context.scene.tool_settings.image_paint
    canvas = image_paint.canvas
    if canvas and canvas.cpp.valid:
        for i, node in enumerate(self.id_data.nodes):
            if (node.bl_idname == "ShaderNodeTexImage") and (node.image == canvas):
                return i
    return -1


def _set_texnode_index(self, value):
    image_paint = bpy.context.scene.tool_settings.image_paint
    nodes = self.id_data.nodes
    if value < len(nodes):
        node = nodes[value]
        if node.bl_idname == "ShaderNodeTexImage":
            image = node.image
            if image and image_paint.canvas != image and image.cpp.valid:
                image_paint.canvas = image


active_texnode_index = bpy.props.IntProperty(
    name="Active Texture", get=_get_texnode_index, set=_set_texnode_index)
