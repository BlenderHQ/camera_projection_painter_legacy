# <pep8 compliant>

import bpy
from mathutils import Vector


SPACE_BEETWEEN_NODES = 50
NODE_FRAME_TEXT = "Camera Painter Added"
NODE_FRAME_COLOR = (0.5, 0.6, 0.8)


def get_nodes_active_output(nodes: bpy.types.bpy_prop_collection):
    """Returns the active output from the node tree nodes"""
    for node in nodes:
        if node.bl_idname == "ShaderNodeOutputMaterial":
            if node.is_active_output:
                return node


def nodes_recursive_search(nodes: bpy.types.bpy_prop_collection, active_output: bpy.types.Node):
    """
    Returns data about a node, its input (color or shader),
    its index from the node tree by searching from the active output
    """
    current_node = active_output
    current_node_index = 0
    current_input_socket = None
    nodes_count = len(nodes)

    while nodes_count > 1:
        if current_node.bl_idname == "ShaderNodeTexImage":
            break
        for i, current_input_socket in enumerate(current_node.inputs):
            if current_input_socket.bl_idname in ("NodeSocketColor", "NodeSocketShader"):
                if current_input_socket.is_linked:
                    current_node = current_input_socket.links[0].from_node
                else:
                    current_input_socket = current_input_socket
                    current_node_index = i
                break
        nodes_count -= 1

    return current_node, current_input_socket, current_node_index


def set_canvas_to_material_diffuse(material: bpy.types.Material, image: bpy.types.Image):
    """Sets canvas as a diffuse texture of the active material"""
    material.use_nodes = True
    material_node_tree = material.node_tree

    nodes = material_node_tree.nodes

    active_output = get_nodes_active_output(nodes)
    if not active_output:
        active_output = material_node_tree.nodes.new(type = "ShaderNodeOutputMaterial")

    current_node, current_input_socket, current_node_index = nodes_recursive_search(nodes, active_output)

    if current_node.bl_idname != "ShaderNodeTexImage" and current_input_socket:
        # Frame around created nodes
        node_frame = None
        for node in nodes:
            if node.label == NODE_FRAME_TEXT:
                node_frame = node
        if not node_frame:
            node_frame = material_node_tree.nodes.new(type = "NodeFrame")

        node_frame.label = NODE_FRAME_TEXT
        node_frame.use_custom_color = True
        node_frame.color = NODE_FRAME_COLOR
        node_frame.select = False

        def create_node(node_type, next_node, node_index):
            """Function to add nodes"""
            new_node = material_node_tree.nodes.new(node_type = node_type)
            new_node_location = Vector(next_node.location) - Vector([new_node.width + SPACE_BEETWEEN_NODES, 0])
            new_node.location = new_node_location
            new_node.parent = node_frame
            new_node.select = False
            material_node_tree.links.new(new_node.outputs[0], next_node.inputs[node_index])
            return new_node

        # In case there was a Shader input
        if current_input_socket.bl_idname == "NodeSocketShader":
            new_bsdf_node = create_node("ShaderNodeBsdfPrincipled", current_node, current_node_index)

            current_node = new_bsdf_node
            current_node_index = 0
            current_input_socket = [n for n in new_bsdf_node.inputs if n.bl_idname == "NodeSocketColor"][0]

        # In case there was a Color input
        if current_input_socket.bl_idname == "NodeSocketColor":
            new_tex_image_node = create_node("ShaderNodeTexImage", current_node, current_node_index)

            current_node = new_tex_image_node

    # If TexImage node is found
    if current_node.bl_idname == "ShaderNodeTexImage":
        current_node.image = image
        return -1
    return 0


def set_material_diffuse_to_canvas(image_paint, material):
    """Sets the diffuse texture of the active material as canvas"""
    node_tree = material.node_tree
    nodes = node_tree.nodes

    active_output = get_nodes_active_output(nodes)
    if not active_output:
        return 1
    _node, _socket, _index = nodes_recursive_search(nodes, active_output)

    if _node.bl_idname == "ShaderNodeTexImage":
        image = _node.image
        if image:
            if image.cpp.valid:
                image_paint.canvas = image
                return -1
            else:
                return 2
    return 3


def operator_execute(self, context):
    """Operator Execution Method"""
    active_object = context.active_object
    scene = context.scene
    image_paint = scene.tool_settings.image_paint

    object_material = active_object.active_material

    if self.reverse:
        if not object_material.use_nodes:
            self.report(type = {'WARNING'}, message = "Active material does not use nodes!")
            return {'CANCELLED'}

        result = set_material_diffuse_to_canvas(image_paint, object_material)
        if result == -1:
            self.report(type = {'INFO'}, message = "Canvas set of diffuse texture")
        elif result == 1:
            self.report(type = {'WARNING'}, message = "The material has no active output!")
        elif result == 2:
            self.report(type = {'WARNING'}, message = "Invalid image found in nodes!")
        elif result == 3:
            self.report(type = {'WARNING'}, message = "Image not found!")

    else:
        result = set_canvas_to_material_diffuse(object_material, image_paint.canvas)
        if result == -1:
            self.report(type = {'INFO'}, message = "Diffuse texture set from canvas")
        else:
            self.report(type = {'WARNING'}, message = "Failed to set diffuse texture from canvas!")
            


    return {'FINISHED'}


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
    
    execute = operator_execute


